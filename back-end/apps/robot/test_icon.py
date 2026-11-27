import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from apps.properties.models import Property
from .asset_reviews import ICON_MOSS_REVIEWS
from .developer_pipeline import JOBS, reconcile_units, run_job
from .extraction.document import ExtractedPage, ExtractionError
from .extraction.dwv import IconTableParser
from .models import TableUnit
from .profiles import get_profile
from .publication import DeveloperPublicationPolicy, MGAPublicationPolicy


def pages():
    return [ExtractedPage(**p) for p in json.loads(
        (Path(__file__).parent / "fixtures/icon-dwv.json").read_text(encoding="utf-8"))]


class IconParserTests(SimpleTestCase):
    def test_complete_real_document_includes_page_continuations_and_reserved_unit(self):
        units = IconTableParser().parse(pages(), JOBS["icon"].context)
        self.assertEqual(len(units), 22)
        self.assertEqual(sum(u.raw["situacao_comercial"] == "disponivel" for u in units), 21)
        by_id = {u.fields["unidade"]: u for u in units}
        self.assertEqual(by_id["301"].fields["andar"], "3")
        self.assertEqual(by_id["301"].fields["valor"], "568097.85")
        self.assertEqual(by_id["1003"].fields["andar"], "10")
        self.assertEqual(by_id["1003"].fields["valor"], "459046.08")
        self.assertEqual(by_id["103"].fields["area_privativa"], "27.59")
        self.assertEqual(by_id["103"].fields["area_total"], "27.59")
        self.assertEqual(by_id["103"].fields["quartos"], 1)
        self.assertEqual(by_id["103"].fields["suites"], 1)
        self.assertEqual(by_id["103"].fields["previsao_entrega"], "2029-09")
        self.assertEqual(by_id["103"].fields["registro_incorporacao"], "5-162.376")
        self.assertIsNone(by_id["205"].fields["valor"])
        self.assertIn("UNIDADE_NAO_DISPONIVEL", by_id["205"].warnings)
        self.assertEqual(by_id["103"].fields["origem_comercial"], "ICON")

    def test_installments_never_replace_missing_total_price(self):
        document = pages()
        document[0].text = document[0].text.replace("R$ 458.933,24", "")
        unit = IconTableParser().parse(document, JOBS["icon"].context)[0]
        self.assertIsNone(unit.fields["valor"])
        self.assertIn("68.839,99", unit.raw["condicoes_pagamento_linha"])

    def test_mismatched_project_does_not_inherit_moss_units(self):
        self.assertEqual(IconTableParser().parse(pages(), {"empreendimento": "Outro empreendimento"}), [])

    def test_reconciliation_detects_missing_units(self):
        document = pages()
        units = IconTableParser().parse(document, JOBS["icon"].context)
        result = {"pages": [{"text": p.text} for p in document], "units": [u.as_dict() for u in units]}
        self.assertTrue(reconcile_units(result)["matched"])
        result["units"].pop()
        self.assertFalse(reconcile_units(result)["matched"])

    def test_visual_reviews_expire_if_file_content_changes(self):
        profile = get_profile(SimpleNamespace(pasta_id=JOBS["icon"].source_id, perfil={}))
        reviewed_id, review = next((fid, r) for fid, r in ICON_MOSS_REVIEWS.items() if r["category"] == "lazer")
        item = {"id": reviewed_id, "name": "8. Coworking.png", "mime_type": "image/png",
                "folder_path": "MOSS/Imagens/TÉRREO", "md5_checksum": review["md5"]}
        self.assertEqual(profile.classify(item)["categoria"], "lazer")
        self.assertNotEqual(profile.classify({**item, "md5_checksum": "changed"})["motivo"], "CHECKSUM_BOUND_VISUAL_REVIEW")
        excluded_id, excluded = next((fid, r) for fid, r in ICON_MOSS_REVIEWS.items() if r["category"] is None)
        self.assertTrue(profile.classify({**item, "id": excluded_id, "md5_checksum": excluded["md5"]})["excluido"])


class IconPipelineTests(TestCase):
    def snapshot(self, content):
        job = JOBS["icon"]
        return {"source": {"pk": 7, "nome": "MOSS / ICON", "pasta_id": job.source_id, "perfil": {}},
                "folders": [{"id": job.source_id, "name": "MOSS", "path": "MOSS", "parent_id": "", "depth": 0}],
                "files": [{"id": fid, "name": name, "mime_type": "application/pdf", "folder_id": job.source_id,
                           "folder_path": "MOSS", "url": "https://drive.google.com/file/d/" + fid,
                           "md5_checksum": hashlib.md5(content).hexdigest()}
                          for fid, name in ((job.table_id, "Tabela MOSS.pdf"), (job.book_id, "Book MOSS.pdf"))]}

    @patch("apps.robot.extraction.service.schedule_location")
    @patch("apps.robot.developer_pipeline.attach_images", return_value={"status": "aguardando_acervo"})
    @patch("apps.robot.developer_pipeline.DocumentExtractor")
    def test_available_units_are_idempotent_and_reserved_unit_is_only_staged(self, extractor, gallery, location):
        extractor.return_value.extract.return_value = pages()
        content = b"fixture"
        report = run_job(JOBS["icon"], self.snapshot(content), content, base_dir=Path("."), apply=True)
        repeated = run_job(JOBS["icon"], self.snapshot(content), content, base_dir=Path("."), apply=True)
        self.assertEqual(len(report["properties"]), 21)
        self.assertEqual(len(report["excluded_units"]), 1)
        self.assertEqual(Property.objects.count(), 21)
        self.assertFalse(any(row["created"] for row in repeated["properties"]))
        self.assertEqual(Property.objects.filter(status="rascunho").count(), 21)
        self.assertIsNone(TableUnit.objects.get(fields__unidade="205").imported_property_id)
        readiness = DeveloperPublicationPolicy("icon").evaluate(Property.objects.first())
        self.assertNotIn("ORIGEM_FONTE_NAO_CONFIRMADA", readiness["issues"])
        self.assertIn("CONFERENCIA_DA_TABELA_PENDENTE", readiness["issues"])
        self.assertFalse(readiness["eligible"])
        self.assertEqual(MGAPublicationPolicy().developer_profile, "mga")

    @patch("apps.robot.developer_pipeline.DocumentExtractor")
    def test_incomplete_extraction_is_blocked_before_database_writes(self, extractor):
        extractor.return_value.extract.return_value = pages()[:1]
        content = b"fixture"
        with self.assertRaises(ExtractionError):
            run_job(JOBS["icon"], self.snapshot(content), content, base_dir=Path("."), apply=True)
        self.assertEqual(Property.objects.count(), 0)

    def test_source_and_checksum_must_match_before_extraction(self):
        content = b"fixture"
        snapshot = self.snapshot(content)
        with self.assertRaises(ExtractionError):
            run_job(JOBS["icon"], snapshot, b"wrong PDF", base_dir=Path("."))
        snapshot["source"]["pasta_id"] = "wrong source"
        with self.assertRaises(ExtractionError):
            run_job(JOBS["icon"], snapshot, content, base_dir=Path("."))
