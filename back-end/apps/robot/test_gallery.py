from io import BytesIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch
from pathlib import Path

from django.test import SimpleTestCase, TestCase, override_settings
from PIL import Image

from apps.properties.models import Property, PropertyImage
from .gallery import CAPS, attach_images, build_plan, scoped_assets
from .models import DriveImageAsset, PropertyImageSelection, TableImport, TableUnit
from .sources import DEFAULT_SOURCES


class GalleryPlanTests(SimpleTestCase):
    def test_caps_order_randomness_and_stable_seed(self):
        assets = [SimpleNamespace(pk=i * 20 + n, file_id=f"id-{i}-{n}", category=category)
                  for i, category in enumerate(CAPS) for n in range(10)]
        signatures = set()
        for seed in range(30):
            plan = build_plan(assets, seed)
            self.assertEqual(plan, build_plan(assets, seed))
            self.assertGreaterEqual(plan["target"], 6)
            self.assertLessEqual(plan["target"], 9)
            self.assertEqual(plan["quotas"]["fachada"], 2)
            self.assertTrue(all(plan["quotas"][category] <= cap for category, cap in CAPS.items()))
            signatures.add(tuple(plan["pools"]["lazer"][:4]))
        self.assertGreater(len(signatures), 1)

    def test_insufficient_inventory_is_never_padded(self):
        plan = build_plan([SimpleNamespace(pk=1, file_id="only", category="internos")], 1)
        self.assertEqual(plan["target"], 1)
        self.assertEqual(plan["quotas"], {"fachada": 0, "lazer": 0, "internos": 1})

    def test_robot_can_normalize_large_original_without_raising_manual_upload_limit(self):
        from django.core.files.base import ContentFile
        from rest_framework.exceptions import ValidationError
        from apps.common.images import prepare_images

        output = BytesIO()
        Image.new("RGB", (20, 20), "blue").save(output, format="PNG")
        raw = output.getvalue() + b"\0" * (11 * 1024 * 1024)
        with self.assertRaises(ValidationError):
            prepare_images([ContentFile(raw, name="large.png")])
        prepared = prepare_images([ContentFile(raw, name="large.png")], max_input_bytes=64 * 1024 * 1024, decoder_thumbnail=True)
        self.assertLess(prepared[0].size, 1024 * 1024)

    def test_large_image_uses_server_side_drive_rendition_and_caches_it(self):
        from .gallery import download_image

        asset = SimpleNamespace(file_id="1234567890image", metadata={"size": 38_000_000, "modified_time": "v1"}, save=Mock())
        service = Mock()
        service._http.request.return_value = (SimpleNamespace(status=200), b"image-content")
        with TemporaryDirectory() as directory, override_settings(BASE_DIR=Path(directory)), \
             patch("apps.robot.drive.drive_service", return_value=service), \
             patch("apps.robot.drive.execute", return_value={"thumbnailLink": "https://lh3.googleusercontent.com/example=s220", "capabilities": {"canDownload": True}}):
            self.assertEqual(download_image(asset), b"image-content")
            self.assertEqual(download_image(asset), b"image-content")
        service._http.request.assert_called_once_with("https://lh3.googleusercontent.com/example=s2560", method="GET")
        self.assertEqual(asset.metadata["rendition"], "drive_thumbnail_2560")
        self.assertNotIn("thumbnailLink", asset.metadata)


class GalleryAttachmentTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        settings = override_settings(MEDIA_ROOT=self.directory.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.property = Property.objects.create(titulo="Makai 101", empreendimento="Makai", unidade="101", tipo="apartamento",
                                                finalidade="venda", valor="1000000", cidade="Cabedelo", bairro="Camboinha")
        self.document = TableImport.objects.create(identity="a" * 64, content_sha256="b" * 64, filename="Tabela Makai.pdf",
            parser_version="test", source_folder_id=DEFAULT_SOURCES[1][1])
        self.unit = TableUnit.objects.create(document=self.document, index=1, imported_property=self.property,
            fields={"empreendimento": "Makai", "unidade": "101"})
        self.assets = []
        for category, count in (("fachada", 3), ("lazer", 7), ("internos", 5)):
            for number in range(count):
                self.assets.append(self.asset(category, f"{category}{number}"))

    def asset(self, category, identifier, **changes):
        data = {"source_id": DEFAULT_SOURCES[1][1], "file_id": identifier, "folder_id": "folder", "name": identifier + ".png",
                "path": "MGA/Makai/Imagens", "mime_type": "image/png", "project_name": "Makai", "project_normalized": "makai",
                "category": category, "url": "https://example.com/image", "metadata": {"avulso": False}}
        data.update(changes)
        return DriveImageAsset.objects.create(**data)

    @staticmethod
    def image(asset):
        output = BytesIO()
        Image.new("RGB", (40, 40), (asset.pk % 255, 80, 90)).save(output, format="PNG")
        return output.getvalue()

    def test_attaches_order_cover_and_never_duplicates_on_repeat(self):
        first = attach_images(self.unit.pk, self.image)
        photos = list(self.property.imagens.all())
        self.assertGreaterEqual(len(photos), 6)
        self.assertLessEqual(len(photos), 9)
        self.assertEqual([p.categoria for p in photos[:2]], ["fachada", "fachada"])
        self.assertEqual([p.ordem for p in photos], list(range(len(photos))))
        self.assertTrue(photos[0].imagem_capa)
        self.assertEqual(sum(p.imagem_capa for p in photos), 1)
        self.assertTrue(all(p.vistoria_pendente for p in photos))
        self.assertEqual([p.categoria for p in photos], sorted([p.categoria for p in photos], key=list(CAPS).index))
        ids = [p.origem_drive_id for p in photos]
        attach_images(self.unit.pk, lambda asset: self.fail("Repeat must not download again"))
        self.assertEqual([p.origem_drive_id for p in self.property.imagens.all()], ids)

    def test_identical_contents_are_not_repeated_to_fill_quota(self):
        raw = self.image(self.assets[0])
        result = attach_images(self.unit.pk, lambda asset: raw)
        self.assertEqual(self.property.imagens.count(), 1)
        self.assertIn("ACERVO_INSUFICIENTE_MINIMO_6", result["warnings"])

    def test_other_project_and_other_apartment_are_excluded(self):
        other = self.asset("internos", "otherproject", project_normalized="outro", project_name="Outro")
        wrong = self.asset("internos", "wrongunit", path="MGA/Makai/APTO 102")
        own = self.asset("internos", "ownunit", path="MGA/Makai/APTO 101")
        selected = {asset.pk for asset in scoped_assets(self.unit)}
        self.assertNotIn(other.pk, selected)
        self.assertNotIn(wrong.pk, selected)
        self.assertIn(own.pk, selected)

    def test_avulsos_same_building_require_exact_unit_when_multiple_listed(self):
        self.document.filename = "Tabela de Avulsos.pdf"
        self.document.save()
        TableUnit.objects.create(document=self.document, index=2, fields={"empreendimento": "Makai", "unidade": "102"})
        DriveImageAsset.objects.update(metadata={"avulso": True})
        own = self.asset("internos", "avulso101", path="MGA/Avulsos/Makai/APTO 101", metadata={"avulso": True})
        wrong = self.asset("internos", "avulso102", path="MGA/Avulsos/Makai/APTO 102", metadata={"avulso": True})
        selected = {asset.pk for asset in scoped_assets(self.unit)}
        self.assertEqual(selected, {own.pk})

    def test_avulso_lot_number_in_two_blocks_is_not_ambiguous_or_mixed(self):
        self.document.filename = "Tabela de Avulsos.pdf"
        self.document.save()
        self.property.unidade = "Quadra K lote 190"
        self.property.save()
        self.unit.fields = {"empreendimento": "Makai", "unidade": "Quadra K lote 190"}
        self.unit.save()
        TableUnit.objects.create(document=self.document, index=2, fields={"empreendimento": "Makai", "unidade": "Quadra L lote 190"})
        generic = self.asset("internos", "lotgeneric", path="MGA/Avulsos/Makai/Lote 190", metadata={"avulso": True})
        own = self.asset("internos", "lotk", path="MGA/Avulsos/Makai/Quadra K/Lote 190", metadata={"avulso": True})
        wrong = self.asset("internos", "lotl", path="MGA/Avulsos/Makai/Quadra L/Lote 190", metadata={"avulso": True})
        self.assertEqual({asset.pk for asset in scoped_assets(self.unit)}, {own.pk})

    def test_manual_images_are_preserved(self):
        photo = PropertyImage.objects.create(imovel=self.property, imagem="manual.jpg", ordem=3, imagem_capa=True)
        result = attach_images(self.unit.pk, lambda asset: self.fail("Manual gallery must not be altered"))
        self.assertEqual(result["status"], "imagens_manuais_preservadas")
        photo.refresh_from_db()
        self.assertEqual(photo.ordem, 3)

    def test_download_failure_is_audited_without_disclosing_credentials(self):
        def broken(asset):
            raise RuntimeError("secret-api-key")
        result = attach_images(self.unit.pk, broken)
        self.assertEqual(result["total"], 0)
        self.assertNotIn("secret-api-key", str(result))
        self.assertTrue(result["errors"])
