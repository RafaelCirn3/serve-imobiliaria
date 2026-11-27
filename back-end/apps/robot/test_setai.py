import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase, TestCase

from .extraction.document import ExtractedPage, ExtractionError
from .extraction.service import inspect_table, stage_table
from .extraction.setai import SetaiTableParser
from .profiles import get_profile
from .sources import DEFAULT_SOURCES


class SetaiParserTests(SimpleTestCase):
    def setUp(self):
        self.pages = [ExtractedPage(**p) for p in json.loads(
            (Path(__file__).parent / "fixtures/setai-table.json").read_text(encoding="utf-8"))]
        self.context = {"empreendimento": "SETAI Sandro Barros", "cidade": "João Pessoa",
                        "bairro": "Cabo Branco", "tipo": "apartamento", "finalidade": "venda"}

    def test_real_grid_preserves_units_total_areas_and_price_date(self):
        units = SetaiTableParser().parse(self.pages, self.context)
        self.assertEqual([u.fields["unidade"] for u in units], ["22", "23", "363", "366", "367", "461", "544", "553"])
        self.assertEqual([u.fields["valor"] for u in units],
                         ["638800.00"]*2 + ["675550.00"]*3 + ["696400.00"] + ["840960.00"]*2)
        self.assertEqual([u.fields["area_total"] for u in units],
                         ["31.44"]*2 + ["22.95"]*3 + ["21.45"] + ["24.44"]*2)
        self.assertTrue(all(u.raw["data_tabela"] == "27/04/2026" for u in units))
        self.assertTrue(all("VIGENCIA_NAO_CONFIRMADA" in u.warnings for u in units))
        self.assertTrue(all(u.fields["origem_comercial"] == "Grupo Pirâmide" for u in units))

    def test_unknown_area_and_price_are_not_inferred(self):
        pages = copy.deepcopy(self.pages)
        pages[0].tables[0][4][2] = "ÁREA"
        pages[0].tables[0][5][4] = "RESERVADO"
        units = SetaiTableParser().parse(pages, self.context)
        self.assertIsNone(units[0].fields["valor"])
        self.assertNotIn("area_total", units[0].fields)
        self.assertIn("NATUREZA_AREA_NAO_CONFIRMADA", units[0].warnings)
        self.assertIn("UNIDADE_NAO_DISPONIVEL", units[0].warnings)

    def test_profile_dispatch_rejects_unknown_parser(self):
        extractor = Mock()
        extractor.extract.return_value = self.pages
        result = inspect_table(b"PDF fixture", "table.pdf", self.context, extractor=extractor, developer_profile="setai")
        self.assertEqual(result["parser_version"], "setai-1.0.0")
        self.assertEqual(len(result["units"]), 8)
        with self.assertRaises(ExtractionError):
            inspect_table(b"PDF fixture", "table.pdf", extractor=extractor, developer_profile="unknown")

    def test_canonical_identity_does_not_relabel_other_developers(self):
        profile = get_profile(SimpleNamespace(pasta_id=DEFAULT_SOURCES[5][1], perfil={}))
        identity = profile.identity("Sandro Barros")
        self.assertEqual(identity.name, "SETAI Sandro Barros")
        self.assertEqual(identity.companies, ("setai",))
        self.assertEqual(profile.identity("Arian").companies, ())
        self.assertEqual(profile.identity("Mondo").companies, ("mga",))


class SetaiStagingTests(TestCase):
    def test_staging_remains_idempotent_with_setai_profile(self):
        result = {"developer_profile": "setai", "parser_version": "setai-1.0.0",
                  "content_sha256": "a"*64, "filename": "TABELA SANDRO BARROS", "context": {},
                  "pages": [], "warnings": [], "units": []}
        first, created = stage_table(result)
        second, repeated = stage_table(result)
        self.assertTrue(created)
        self.assertFalse(repeated)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.developer_profile, "setai")
