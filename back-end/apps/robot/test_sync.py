from copy import deepcopy
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from types import SimpleNamespace
import hashlib
import json

from django.test import SimpleTestCase, TestCase
from apps.locations.addressing import AddressNormalizer
from apps.properties.models import Property
from .extraction.defaults import CommercialDefaults
from .extraction.document import ExtractedPage
from .extraction.mga import MGATableParser
from .extraction.service import stage_table, commit_unit
from .models import TableImport, TableUnit, DriveImageAsset
from .synchronization import MGASynchronizer
from .gallery import scoped_assets, download_image
from .test_mga import extracted, FIXTURES


class CommercialDefaultTests(SimpleTestCase):
    def test_five_integer_digits_is_rental_six_is_sale_and_explicit_always_wins(self):
        for price,purpose in (("99999.99","aluguel"),("100000.00","venda"),("2820000.00","venda")):
            fields,decisions=CommercialDefaults.apply({"valor":price,"finalidade":""},avulso=True)
            self.assertEqual(fields["finalidade"],purpose)
            self.assertEqual(len(decisions),1)
        fields,decisions=CommercialDefaults.apply({"valor":"120000.00","finalidade":"aluguel"},avulso=True)
        self.assertEqual(fields["finalidade"],"aluguel")
        self.assertEqual(decisions,[])
        self.assertNotIn("finalidade",CommercialDefaults.apply({"valor":"10000"},avulso=False)[0])
        for price in (None,"NaN","-1","0"):
            self.assertNotIn("finalidade",CommercialDefaults.apply({"valor":price},avulso=True)[0])

    def test_bananeiras_centro_keeps_raw_address(self):
        raw="Rua Pedro Gondim Sitio Bezerros, Bananeiras - PB"
        fields=AddressNormalizer.parse({"endereco":raw,"bairro":"Sítio Bezerros"})
        self.assertEqual(fields["bairro"],"Centro")
        self.assertEqual(fields["endereco"],raw)

    def test_confirmed_mondo_alias_preserves_explicit_rental_pages(self):
        doc=json.loads((FIXTURES/"native-tables.json").read_text(encoding="utf-8"))[5]
        units=MGATableParser().parse([ExtractedPage(**p) for p in doc["pages"]],{"empreendimento":"Mondo 2"})
        self.assertEqual({u.fields["empreendimento"] for u in units},{"Mondo"})
        self.assertEqual({u.fields["bairro"] for u in units},{"Bessa"})
        self.assertEqual(sum(u.fields["finalidade"]=="aluguel" for u in units),3)
        self.assertEqual(sum(u.fields["finalidade"]=="venda" for u in units),17)


class SyncTests(TestCase):
    def test_public_pdf_fallback_requires_matching_drive_checksum(self):
        from googleapiclient.errors import HttpError
        from httplib2 import Response
        from unittest.mock import Mock
        from django.test import override_settings

        content = b"%PDF-1.4\nverified test document"
        file = {"id": "public-pdf", "name": "Tabela.pdf", "size": len(content),
                "md5_checksum": hashlib.md5(content).hexdigest()}
        service = Mock()
        downloader = Mock()
        downloader.next_chunk.side_effect = HttpError(Response({"status": "429"}), b"blocked")
        with TemporaryDirectory() as directory, override_settings(BASE_DIR=Path(directory)), \
                patch("apps.robot.synchronization.drive_service", return_value=service), \
                patch("googleapiclient.http.MediaIoBaseDownload", return_value=downloader), \
                patch("apps.robot.synchronization.urlopen", return_value=BytesIO(content)):
            self.assertEqual(MGASynchronizer().content(file), content)
            self.assertEqual((Path(directory) / "reports/mga/input/public-pdf.pdf").read_bytes(), content)

    def test_sync_status_requires_admin_and_returns_checkpoint(self):
        from django.contrib.auth import get_user_model
        from django.test import override_settings
        from rest_framework.test import APIClient
        client = APIClient()
        url = "/api/admin/robot/mga/extracoes/sincronizacao/"
        self.assertIn(client.get(url).status_code, (401, 403))
        admin = get_user_model().objects.create_superuser(username="sync-admin", password="test")
        client.force_authenticate(admin)
        with TemporaryDirectory() as directory, override_settings(BASE_DIR=Path(directory)):
            self.assertEqual(client.get(url).json()["status"], "nao_executada")
            checkpoint = Path(directory) / "reports/mga/sync-result.json"
            MGASynchronizer.checkpoint(checkpoint, {"finished_at": "2026-11-25", "created": 0, "existing": 264, "errors": []})
            response = client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "concluida")
            self.assertEqual(response.json()["existing"], 264)

    def test_drive_download_failure_retries_supported_rendition(self):
        from django.test import override_settings
        from googleapiclient.errors import HttpError
        from httplib2 import Response
        from unittest.mock import Mock
        asset = DriveImageAsset(file_id="valid_image_id_123", metadata={"size": 100}, name="photo.jpg")
        asset.save = Mock()
        service = Mock()
        service._http.request.return_value = (SimpleNamespace(status=200), b"photo-content")
        with TemporaryDirectory() as directory, override_settings(BASE_DIR=Path(directory)), \
                patch("apps.robot.drive.drive_service", return_value=service), \
                patch("apps.robot.drive.execute", return_value={"capabilities": {"canDownload": True}, "thumbnailLink": "https://lh3.googleusercontent.com/photo=s220"}), \
                patch("googleapiclient.http.MediaIoBaseDownload") as downloader:
            downloader.return_value.next_chunk.side_effect = HttpError(Response({"status": "403"}), b"unavailable")
            self.assertEqual(download_image(asset), b"photo-content")
            service._http.request.assert_called_once_with("https://lh3.googleusercontent.com/photo=s2560", method="GET")

    def test_refresh_keeps_document_and_units_without_overwriting_published_price(self):
        result=extracted()
        document,_=stage_table(result,drive_file_id="file")
        first=document.units.first()
        with patch("apps.robot.extraction.service.schedule_location"):
            property,_=commit_unit(first.pk,with_images=False)
        property.status="publicado"
        property.save()
        updated=deepcopy(result)
        updated["units"][0]["fields"]["valor"]="3000000.00"
        refreshed=MGASynchronizer().refresh(updated,"source","file")
        self.assertEqual(refreshed.pk,document.pk)
        self.assertEqual(TableImport.objects.count(),1)
        self.assertEqual(TableUnit.objects.count(),2)
        property.refresh_from_db()
        self.assertEqual(property.valor,2820000)
        self.assertEqual(refreshed.units.first().fields["valor"],"3000000.00")

    def test_complementary_mondo_assets_are_eligible_but_avulsos_never_cross_sources(self):
        property=Property.objects.create(titulo="Mondo",empreendimento="Mondo",construtora="MGA Construções",unidade="101",tipo="apartamento",finalidade="venda",cidade="João Pessoa",bairro="Bessa",valor=200000)
        doc=TableImport.objects.create(identity="sync-photo",content_sha256="hash",filename="MONDO 2.pdf",source_folder_id="catalog",parser_version="test")
        unit=TableUnit.objects.create(document=doc,index=1,fields={},imported_property=property)
        asset=DriveImageAsset.objects.create(source_id="mga",file_id="photo",folder_id="folder",name="Fachada.jpg",path="Mondo/Fachada",mime_type="image/jpeg",project_name="Mondo",project_normalized="mondo",category="fachada",url="https://example.com",metadata={"identity":{"companies":["mga"]}})
        self.assertIn(asset.pk,{a.pk for a in scoped_assets(unit)})
        doc.filename="Tabela de avulsos.pdf"
        doc.save()
        self.assertNotIn(asset.pk,{a.pk for a in scoped_assets(unit)})
