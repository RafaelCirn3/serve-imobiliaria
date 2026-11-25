import asyncio
from copy import deepcopy
from io import StringIO
from importlib import import_module
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.properties.models import Property
from .extraction.document import DocumentExtractor, ExtractedPage, ExtractionError
from .extraction.mga import MGATableParser, decimal_br
from .extraction.service import commit_unit, inspect_table, review_unit, stage_table, validation_issues
from .models import ImportedUnitIdentity, TableImport

FIXTURES = Path(__file__).parent / "fixtures" / "mga"
PDF = FIXTURES / "avulsos-novembro-2026.pdf"


def extracted(context=None):
    return inspect_table(PDF.read_bytes(), PDF.name, context=context or {"finalidade": "venda"}, allow_ocr=False)


class MGAExtractionTests(SimpleTestCase):
    def test_currency_is_decimal_and_distinguishes_total_from_installments(self):
        for value, expected in (("R$ 2 .820.000,00", "2820000.00"), ("RS 370.000,00", "370000.00"),
                                ("R$ 5 27.286,81", "527286.81"), ("", None), ("VENDIDO", None), ("123,4O", None), ("-1,00", None)):
            self.assertEqual(decimal_br(value), expected)

    def test_real_avulsos_native_text_does_not_call_ocr(self):
        with patch.object(DocumentExtractor, "ocr", side_effect=AssertionError("native text must be preferred")):
            result = extracted()
        self.assertEqual(len(result["units"]), 2)
        first, second = [unit["fields"] for unit in result["units"]]
        self.assertEqual(first["unidade"], "2302")
        self.assertEqual(first["valor"], "2820000.00")
        self.assertEqual(first["area_informada"], "300.00")
        self.assertEqual(first["cidade"], "João Pessoa")
        self.assertEqual(first["bairro"], "Brisamar")
        self.assertEqual(first["tipo"], "cobertura")
        self.assertEqual(first["vagas"], 4)
        self.assertEqual(first["construtora"], "")
        self.assertEqual(second["valor"], "370000.00")
        self.assertEqual(second["medidas"], "16x25m")
        self.assertEqual(second["tipo"], "terreno")
        self.assertEqual(second["bairro"], "")

    def test_real_nine_layouts_and_tower_identity(self):
        documents = json.loads((FIXTURES / "native-tables.json").read_text(encoding="utf-8"))
        results = []
        for document in documents:
            pages = [ExtractedPage(**page) for page in document["pages"]]
            results.append(MGATableParser().parse(pages, document["context"]))
        self.assertEqual([len(units) for units in results], [2, 170, 20, 27, 2, 20, 6, 7, 16])
        elevare = results[1]
        self.assertEqual({u.fields["torre"] for u in elevare if u.fields["unidade"] == "201"}, {"A", "B"})
        unit = next(u for u in elevare if u.fields["unidade"] == "202" and u.fields["torre"] == "A")
        self.assertEqual(unit.fields["valor"], "2131246.64")
        self.assertEqual(decimal_br(unit.raw["condicoes_pagamento"]["SINAL"]), "213124.66")
        self.assertEqual(sum(u.fields["valor"] is None for u in elevare), 48)
        rentals = [u for u in results[5] if u.fields["finalidade"] == "aluguel"]
        self.assertEqual(len(rentals), 3)
        self.assertTrue(all(u.fields["tipo"] == "comercial" for u in rentals))

    def test_real_ocr_coordinates_recover_two_rows_and_require_review(self):
        pages = [ExtractedPage(**page) for page in json.loads((FIXTURES / "avulsos-ocr-pages.json").read_text(encoding="utf-8"))]
        units = MGATableParser().parse(pages, {"finalidade": "venda"})
        self.assertEqual(len(units), 2)
        self.assertEqual([unit.fields["valor"] for unit in units], ["2820000.00", "370000.00"])
        self.assertTrue(all("OCR_REQUER_CONFERENCIA" in unit.warnings for unit in units))

    def test_elevare_merged_header_preserves_all_122_complete_prices(self):
        documents = json.loads((FIXTURES / "native-tables.json").read_text(encoding="utf-8"))
        document = documents[1]
        units = MGATableParser().parse([ExtractedPage(**p) for p in document["pages"]], document["context"])
        priced = [u for u in units if u.fields["valor"]]
        self.assertEqual(len(priced), 122)
        self.assertTrue(all(float(u.fields["valor"]) > 1000000 for u in priced))
        unit = next(u for u in units if u.fields["unidade"] == "1902" and u.fields["torre"] == "B")
        self.assertEqual(unit.fields["valor"], "2122036.00")

    def test_elevare_footer_applies_to_units_on_every_page(self):
        document = json.loads((FIXTURES / "native-tables.json").read_text(encoding="utf-8"))[1]
        units = MGATableParser().parse([ExtractedPage(**p) for p in document["pages"]],
            {**document["context"], "cidade": "João Pessoa"})
        self.assertEqual(len(units), 170)
        for unit in units:
            self.assertEqual(unit.fields["previsao_entrega"], "2031-12")
            self.assertEqual(unit.fields["area_total"], unit.fields["area_informada"])
            self.assertEqual(unit.fields["bairro"], "Altiplano Cabo Branco")
            self.assertEqual(unit.fields["endereco"], "Rua Josita Almeida, 373, Altiplano Cabo Branco")
            self.assertEqual(unit.fields["quartos"], unit.fields["suites"])
            self.assertTrue(unit.fields["andar"].isdigit())
            self.assertEqual(unit.raw["documento"][0]["page"], 4)

    def test_ocr_is_fallback_for_image_and_no_ocr_fails_explicitly(self):
        from PIL import Image
        from io import BytesIO

        buffer = BytesIO()
        Image.new("RGB", (200, 100), "white").save(buffer, format="PNG")
        with patch.object(DocumentExtractor, "ocr", return_value=[]) as ocr:
            pages = DocumentExtractor().extract(buffer.getvalue(), "scan.png")
        ocr.assert_called_once()
        self.assertEqual(pages[0].method, "ocr")
        with self.assertRaises(ExtractionError):
            DocumentExtractor().extract(buffer.getvalue(), "scan.png", allow_ocr=False)
        with self.assertRaises(ExtractionError):
            DocumentExtractor().extract(b"bad file", "bad.pdf")


class MGAImportTests(TestCase):
    def test_preparation_links_images_unless_explicitly_deferred(self):
        source = next(d for d in json.loads((FIXTURES / "native-tables.json").read_text(encoding="utf-8"))
                      if d["context"].get("empreendimento") == "Makai")
        pages = [ExtractedPage(**page) for page in source["pages"]]
        content = b"Makai fixture"
        with patch.object(DocumentExtractor, "extract", return_value=pages):
            result = inspect_table(content, "TABELA MAKAI.pdf", {**source["context"], "finalidade": "venda", "construtora": "MGA"})
        stage_table(result, drive_file_id="fixture")
        command = import_module("apps.robot.management.commands.preparar-mga")
        with TemporaryDirectory() as directory, override_settings(BASE_DIR=Path(directory)):
            path = Path(directory) / "reports/mga/input/fixture.pdf"
            path.parent.mkdir(parents=True)
            path.write_bytes(content)
            with patch.object(command, "inspect_table", return_value=result), patch("apps.robot.extraction.service.schedule_images") as images:
                call_command("preparar-mga", empreendimento="Makai", aplicar=True, output=Path(directory)/"report.json", stdout=StringIO())
                self.assertEqual(images.call_count, 2)
                images.reset_mock()
                call_command("preparar-mga", "--empreendimento", "Makai", "--aplicar", "--sem-imagens", output=Path(directory)/"report.json", stdout=StringIO())
                images.assert_not_called()
                self.assertEqual(Property.objects.count(), 2)

    def test_project_import_enables_grouping_but_avulsos_do_not(self):
        documents = json.loads((FIXTURES / "native-tables.json").read_text(encoding="utf-8"))
        source = next(d for d in documents if d["context"].get("empreendimento") == "Makai")
        pages = [ExtractedPage(**page) for page in source["pages"]]
        with patch.object(DocumentExtractor, "extract", return_value=pages):
            result = inspect_table(b"project fixture", "TABELA MAKAI.pdf", {**source["context"], "finalidade": "venda", "construtora": "MGA Construções"})
        document, _ = stage_table(result)
        property, _ = commit_unit(document.units.first().pk)
        self.assertTrue(property.agrupar_publicacao)
        self.assertTrue(property.grupo_publicacao)
        avulsos, _ = stage_table(extracted())
        property, _ = commit_unit(avulsos.units.first().pk)
        self.assertFalse(property.agrupar_publicacao)
        self.assertEqual(property.grupo_publicacao, "")

    def test_price_repair_is_idempotent_and_preserves_published_properties(self):
        result = extracted()
        legacy = deepcopy(result)
        legacy["units"][0]["fields"]["valor"] = "2.00"
        legacy["units"][0]["raw"]["valor"] = "R$ 2"
        document, _ = stage_table(legacy, drive_file_id="fixture")
        unit = document.units.first()
        with TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "fixture.pdf").write_bytes(PDF.read_bytes())
            args = dict(input_dir=path, cache_dir=path / "cache", output=path / "report.json", stdout=StringIO())
            call_command("corrigir-precos-mga", **args)
            unit.refresh_from_db()
            self.assertEqual(unit.fields["valor"], "2.00")
            call_command("corrigir-precos-mga", aplicar=True, **args)
            unit.refresh_from_db()
            self.assertEqual(unit.fields["valor"], "2820000.00")
            self.assertEqual(len(unit.evidence["price_corrections"]), 1)
            call_command("corrigir-precos-mga", aplicar=True, **args)
            self.assertEqual(json.loads(args["output"].read_text())["changes"], [])
            property, _ = commit_unit(unit.pk)
            property.status = "publicado"
            property.save()
            unit.fields["valor"] = "2.00"
            unit.save()
            call_command("corrigir-precos-mga", aplicar=True, **args)
            self.assertEqual(len(json.loads(args["output"].read_text())["blocked"]), 1)
            property.refresh_from_db()
            self.assertEqual(property.valor, 2820000)

    def test_staging_and_draft_import_are_idempotent(self):
        result = extracted()
        document, created = stage_table(result)
        self.assertTrue(created)
        same, created = stage_table(result)
        self.assertFalse(created)
        self.assertEqual(document.pk, same.pk)
        unit = document.units.order_by("index").first()
        property, created = commit_unit(unit.pk)
        self.assertTrue(created)
        self.assertEqual(property.status, "rascunho")
        self.assertEqual(property.valor, 2820000)
        self.assertEqual(property.unidade, "2302")
        self.assertEqual(property.origem_comercial, "MGA Construções")
        self.assertEqual(property.construtora, "")
        same_property, created = commit_unit(unit.pk)
        self.assertFalse(created)
        self.assertEqual(property.pk, same_property.pk)
        self.assertEqual(Property.objects.count(), 1)
        self.assertFalse(Property.objects.filter(status="publicado").exists())

    def test_unknown_location_blocks_then_review_can_import(self):
        document, _ = stage_table(extracted())
        unit = document.units.order_by("index").last()
        self.assertIn("bairro", validation_issues(unit))
        with self.assertRaises(ValidationError):
            commit_unit(unit.pk)
        review_unit(unit.pk, {"bairro": "Sítio Bezerros"}, approve=True)
        property, created = commit_unit(unit.pk)
        self.assertTrue(created)
        self.assertEqual(property.tipo, "terreno")
        self.assertEqual(property.area_informada, 400)
        self.assertIsNone(property.area_privativa)

    def test_new_document_does_not_overwrite_existing_price(self):
        result = extracted()
        document, _ = stage_table(result)
        first = document.units.order_by("index").first()
        property, _ = commit_unit(first.pk)
        changed = deepcopy(result)
        changed["content_sha256"] = "1" * 64
        changed["units"][0]["fields"]["valor"] = "9999999.00"
        newer, _ = stage_table(changed)
        same, created = commit_unit(newer.units.order_by("index").first().pk)
        self.assertFalse(created)
        self.assertEqual(same.pk, property.pk)
        property.refresh_from_db()
        self.assertEqual(property.valor, 2820000)

    def test_ocr_needs_explicit_approval_and_never_accepts_publish_field(self):
        result = extracted()
        result["units"][0]["warnings"].append("OCR_REQUER_CONFERENCIA")
        document, _ = stage_table(result)
        unit = document.units.order_by("index").first()
        with self.assertRaises(ValidationError):
            commit_unit(unit.pk)
        with self.assertRaises(ValidationError):
            review_unit(unit.pk, {"status": "publicado"}, approve=True)
        review_unit(unit.pk, {}, approve=True)
        property, _ = commit_unit(unit.pk)
        self.assertEqual(property.status, "rascunho")

    def test_cli_applies_drafts_and_repeat_does_not_duplicate(self):
        with TemporaryDirectory() as directory:
            context = Path(directory) / "context.json"
            context.write_text('{"finalidade":"venda"}', encoding="utf-8")
            args = dict(arquivo=PDF, contexto=context, aplicar=True, sem_ocr=True, cache_dir=Path(directory) / "cache", output=Path(directory) / "result.json", stdout=StringIO())
            call_command("robot-mga", **args)
            result = json.loads(args["output"].read_text(encoding="utf-8"))
            self.assertEqual(result["created"], 1)
            self.assertEqual(result["pending"], 1)
            call_command("robot-mga", **args)
            result = json.loads(args["output"].read_text(encoding="utf-8"))
            self.assertEqual(result["existing"], 1)
            self.assertEqual(Property.objects.count(), 1)

    def test_api_requires_admin_and_upload_review_import_flow(self):
        client = APIClient()
        url = "/api/admin/robot/mga/extracoes/"
        self.assertIn(client.get(url).status_code, (401, 403))
        user = get_user_model().objects.create_user(username="robot-admin", password="test", is_staff=True)
        client.force_authenticate(user=user)
        file = SimpleUploadedFile(PDF.name, PDF.read_bytes(), content_type="application/pdf")
        response = client.post(url, {"arquivo": file, "contexto": '{"finalidade":"venda"}', "ocr": "false"}, format="multipart")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(response.data["units"]), 2)
        unit_id = response.data["units"][0]["id"]
        with patch("apps.robot.gallery.attach_after_commit") as gallery, self.captureOnCommitCallbacks(execute=True):
            response = client.post(f"/api/admin/robot/mga/unidades/{unit_id}/importar/")
        gallery.assert_called_once_with(unit_id)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["status"], "rascunho")
        self.assertEqual(client.get("/api/imoveis/").data["count"], 0)
        other = get_user_model().objects.create_user(username="ordinary", password="test")
        client.force_authenticate(user=other)
        self.assertEqual(client.get(url).status_code, 403)

    def test_zero_price_cannot_be_imported(self):
        document, _ = stage_table(extracted())
        unit = document.units.order_by("index").first()
        with self.assertRaises(ValidationError):
            review_unit(unit.pk, {"valor": "0.00"}, approve=True)


class MGAMCPTests(SimpleTestCase):
    def test_official_mcp_sdk_registers_the_four_tools(self):
        from .mcp_server import create_server

        server = create_server()
        tools = asyncio.run(server.list_tools())
        self.assertEqual({tool.name for tool in tools}, {"mga_extrair_tabela", "mga_consultar_extracao", "mga_revisar_unidade", "mga_importar_rascunho"})
