from copy import deepcopy
import csv
from importlib import import_module
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase
from openpyxl import Workbook, load_workbook

from .audit_report import candidate, metrics, write_filter_report
from .inventory import read_inventory
from .mapping import annotate_inventory, audit_duplicates
from .models import DriveSource
from .profile_defaults import PROFILES
from .profiles import SourceProfile, TABLE_MIMES, get_profile, normalize
from .quality import evaluate_sample, write_sample
from .report import atomic_save, write_inventory
from .sources import DEFAULT_SOURCES
from .tests import FakeDrive


FIXTURE = Path(__file__).parent / "fixtures" / "drive_regression_v1.json"


def fixtures():
    return [(SimpleNamespace(pk=None, **entry["source"]), entry["folders"], entry["files"])
            for entry in json.loads(FIXTURE.read_text(encoding="utf-8"))]


def synthetic(index, path, name, mime="image/jpeg"):
    source = SimpleNamespace(pk=None, nome="Teste", pasta_id=DEFAULT_SOURCES[index][1])
    folders = []
    parts = path.split("/")
    for depth, value in enumerate(parts):
        folders.append({"id": str(depth), "name": value, "path": "/".join(parts[:depth + 1]), "parent_id": str(depth - 1) if depth else "",
                        "depth": depth, "url": "https://example.com/folder"})
    item = {"id": "file", "folder_id": str(len(parts) - 1), "folder_path": path, "name": name, "mime_type": mime,
            "size": 100, "modified_time": "2026-11-24", "url": "https://example.com/file"}
    annotate_inventory(source, folders, [item])
    return source, folders, [item]


class ContextRegressionTests(SimpleTestCase):
    def test_real_eight_mga_tables_recovered_with_correct_identity_and_ids(self):
        source, folders, files = fixtures()[1]
        annotate_inventory(source, folders, files)
        expected = {
            "11HOD-JY6Hx3fN-kl6jsGQlI4O7qPoTnK": "Makai", "17ZheY1d99Qo4nO6wxi-pmVjFkIqRXsGu": "Essenza Park",
            "17cuE_jX9Eim6L9PHVcqybVt3C8N9xZff": "Elevare", "1AxTcugGEb8j9c7A-n24wjeUdxsiB4YOF": "Mondo",
            "1YVwfC8RPo88FRqMub5BmdSS070gm7G97": "Lumini", "1c-YHxYh1Y48t8LH3o-0xib5dR-v5AUnv": "Soho",
            "1qCaK2PTeK-7g0msWooFgnh8BgXcIEyy7": "Soleil", "1qNmVTuvn8oFRahnyZf98j6Tt4thZzeha": "Sens",
        }
        found = {item["id"]: item for item in files}
        for file_id, name in expected.items():
            with self.subTest(file_id=file_id):
                item = found[file_id]
                self.assertTrue(candidate(item))
                self.assertEqual(item["classification"]["categoria"], "tabela_precos")
                self.assertEqual(normalize(item["project_identity"]["name"]), normalize(name))
                self.assertIn("COMMERCIAL_TABLE_MATCH", item["classification"]["regras"])

    def test_mixed_folder_cases_and_true_technical_exclusions(self):
        for folder, name, mime, category in (
            ("Imagens e Plantas", "Fachada.jpg", "image/jpeg", "fachada"),
            ("Imagens e Vídeo", "Piscina.png", "image/png", "lazer"),
            ("Imagens e Vídeo", "Video.mp4", "video/mp4", None),
            ("Plantas", "Planta baixa.pdf", "application/pdf", None),
            ("Tabela Book Imagens e Plantas", "Tabela.pdf", "application/pdf", "tabela_precos"),
            ("Renders e Plantas/RENDERS", "Academia.jpg", "image/jpeg", "lazer"),
        ):
            with self.subTest(folder=folder, name=name):
                _, _, files = synthetic(1, f"MGA/Projeto/{folder}", name, mime)
                self.assertEqual(files[0]["classification"]["categoria"], category)
                self.assertEqual(candidate(files[0]), category is not None)

    def test_books_and_unit_descriptions_are_not_tables(self):
        source, folders, files = fixtures()[1]
        annotate_inventory(source, folders, files)
        for file_id in ("13WMAdMSHpt_bjNpS1Nsa60ttPbDgwOeg", "1V6MtHw_FWeNwpejX_IcT2zyF4U9ZFz95"):
            item = next(item for item in files if item["id"] == file_id)
            self.assertFalse(candidate(item))
            self.assertEqual(item["classification"]["motivo"], "TECHNICAL_DOCUMENT")

    def test_real_twenty_organizational_table_identities_are_resolved(self):
        cases = fixtures()
        for index, count in ((0, 2), (3, 8), (5, 10)):
            source, folders, files = cases[index]
            annotate_inventory(source, folders, files)
            tables = [item for item in files if item["classification"]["categoria"] == "tabela_precos"]
            expected_ids = {"1T9pgHxDKOMaNu79s-AEqbnPJkb83ERnU", "1vzpOSuYwIaWFd058ASt8T5K1kZ-AppXx"} if index == 0 else None
            if expected_ids:
                tables = [item for item in tables if item["id"] in expected_ids]
            self.assertEqual(len(tables), count)
            for item in tables:
                self.assertFalse(get_profile(source).is_organizational(item["project_identity"]["name"]))
                if not item["project_identity"]["name"]:
                    self.assertIn("UNKNOWN_PROJECT", item["classification"]["motivos_revisao"])
            if index == 0:
                self.assertEqual({normalize(item["project_identity"]["name"]) for item in tables}, {"alameda dos ventos", "terraco das dunas"})
            if index == 5:
                names = {normalize(item["project_identity"]["name"]) for item in tables}
                self.assertTrue({"mondo", "arian", "mirai", "new wave"} <= names)

    def test_commercial_mimes_and_no_extension(self):
        for mime in TABLE_MIMES:
            _, _, files = synthetic(1, "MGA/Projeto/TABELA", "Tabela Projeto", mime)
            self.assertEqual(files[0]["classification"]["categoria"], "tabela_precos")

    def test_normalization_preserves_identity_numbers(self):
        for name, expected in (("Cópia de 1- FACHADA DIURNA.jpg", "fachada diurna"), ("FACHADA_FRONTAL- 8K.png", "fachada frontal 8k"),
                               ("2026.06 - Raveo (230 und)", "raveo"), ("Elevare: Tabela | Book | Imagens & Plantas", "elevare"),
                               ("Mondo 2", "mondo 2"), ("Farol 137", "farol 137"), ("Apartamento 302", "apartamento 302"),
                               ("TF Breezy 3 Ruas", "tf breezy 3 ruas")):
            self.assertEqual(normalize(name), expected)

    def test_semantic_specificity_and_ambiguous_categories(self):
        for name, category in (("Sala de jogos.jpg", "lazer"), ("Sala de massagem.jpg", "lazer"), ("Cozinha gourmet comum.jpg", "lazer"),
                               ("Piscina privativa.jpg", "internos"), ("Cozinha privativa.jpg", "internos"), ("Sala de estar.jpg", "internos")):
            _, _, files = synthetic(1, "MGA/Projeto/IMAGENS", name)
            self.assertEqual(files[0]["classification"]["categoria"], category)
        _, _, files = synthetic(1, "MGA/Projeto/IMAGENS", "Piscina e cozinha.jpg")
        self.assertIsNone(files[0]["classification"]["categoria"])
        self.assertIn("AMBIGUOUS_CATEGORY", files[0]["classification"]["motivos_revisao"])

    def test_tf_hierarchy_and_generic_filename(self):
        _, _, files = synthetic(8, "TF/1. Lançamentos/TF CONECT/1. FACHADA", "44836824-9A75-4D31.jpg")
        self.assertEqual(files[0]["project_identity"]["name"], "TF CONECT")
        self.assertEqual(files[0]["classification"]["categoria"], "fachada")
        self.assertIn("CATEGORY_FOLDER_MATCH", files[0]["classification"]["regras"])

    def test_arc_video_room_is_image_not_video_asset(self):
        for name in ("SALA DE VÍDEO.jpg", "SALA DE PODCAST.jpg", "SALA DE REUNIÃO.jpg", "LOUNGE COZINHA.jpg", "BUSINESS CLUB_LIVING.jpg"):
            _, _, files = synthetic(2, "ARC/IMAGENS/Imagens e Vídeo", name)
            self.assertTrue(candidate(files[0]))
        _, _, files = synthetic(2, "ARC/IMAGENS", "Video.mp4", "video/mp4")
        self.assertFalse(candidate(files[0]))

    def test_sold_projects_are_catalogued_but_not_available(self):
        _, _, files = synthetic(11, "Bauten/Áurea - 100% vendido - Cabo Branco/IMAGENS", "PISCINA+AUREA.jpg")
        c = files[0]["classification"]
        self.assertTrue(candidate(files[0]))
        self.assertFalse(c["elegivel_anuncio"])
        self.assertIn("SOLD_PROJECT", c["motivos_revisao"])

    def test_three_confidences_and_modes_are_independent(self):
        for index, name, mime in ((4, "fachada.jpg", "image/jpeg"), (12, "EXTERNAS.jpg", "image/jpeg"),
                                  (13, "Tabela de avulsos.pdf", "application/pdf")):
            _, _, files = synthetic(index, "Fonte/Imagens", name, mime)
            c, identity = files[0]["classification"], files[0]["project_identity"]
            self.assertGreater(c["confianca_categoria"]["pontuacao"], 0)
            self.assertEqual(identity["developer_confidence"]["pontuacao"], 0)
            self.assertEqual(c["status_decisao"], "REVISAO")

    def test_alias_conflict_is_not_merged_and_no_fuzzy_merge(self):
        config = deepcopy(PROFILES[1])
        config["canonical_projects"] = [{"key": "one", "name": "Elevare", "aliases": []}, {"key": "two", "name": "Other", "aliases": ["Elevare"]}]
        self.assertEqual(SourceProfile(config).identity("Elevare").confidence, "conflito")
        self.assertNotEqual(SourceProfile(PROFILES[1]).identity("Elevare II").key, "mga-tropical:elevare")

    def test_conversion_flags_for_heif_tiff_psd_and_no_physical_download(self):
        for mime in ("image/heif", "image/heic", "image/tiff", "image/vnd.adobe.photoshop"):
            _, _, files = synthetic(1, "MGA/Projeto/IMAGENS", "Fachada", mime)
            self.assertTrue(candidate(files[0]))
            self.assertTrue(files[0]["classification"]["requires_conversion"])

    def test_all_sixteen_profiles_are_deterministic_and_account_for_every_file(self):
        for source, folders, files in fixtures():
            annotate_inventory(source, folders, files)
            before = deepcopy(files)
            annotate_inventory(source, folders, files)
            self.assertEqual(before, files)
            m = metrics([(source, folders, files)])
            self.assertEqual(m["originais"], m["selecionados"] + m["descartados"] + m["revisao"])
            for item in files:
                self.assertIn(item["classification"]["status_decisao"], ("SELECIONADO", "DESCARTADO", "REVISAO"))

    def test_progressive_duplicates_preserve_origins_and_do_not_confirm_names(self):
        first = synthetic(1, "MGA/Projeto/IMAGENS", "fachada.jpg")
        second = synthetic(10, "Elevare/IMAGENS", "fachada.jpg")
        rows = audit_duplicates([first, second])
        self.assertEqual({row["kind"] for row in rows}, {"DRIVE_ID", "NAME_SIZE"})
        named = next(row for row in rows if row["kind"] == "NAME_SIZE")
        self.assertEqual(named["decision"], "POTENTIAL_DUPLICATE_REVIEW")
        self.assertEqual(len(named["references"]), 2)

    def test_audit_tabs_trace_original_files_and_atomic_output(self):
        inventories = [synthetic(1, "MGA/Projeto/PLANTAS", "Planta.pdf", "application/pdf"),
                       synthetic(4, "Urban/Imagens", "fachada.jpg")]
        with TemporaryDirectory() as directory:
            output = Path(directory) / "audit.xlsx"
            write_filter_report(output, inventories, {"run_id": "test", "errors": []})
            book = load_workbook(output)
            self.assertEqual(book.sheetnames, ["Resumo", "Fontes", "Pastas", "Arquivos", "Descartados", "Revisão", "Empreendimentos", "Cobertura", "Duplicidades", "Regras", "Auditoria"])
            self.assertEqual(book["Descartados"].max_row, 2)
            self.assertEqual(book["Revisão"].max_row, 2)
            self.assertIn("TECHNICAL_DOCUMENT", str(list(book["Descartados"].values)))
            self.assertEqual(book["Arquivos"]["G2"].value, "file")
            self.assertIn("confianca_categoria_detalhes", [cell.value for cell in book["Arquivos"][1]])
            book.close()
            previous = output.read_bytes()
            with patch.object(Workbook, "save", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    atomic_save(Workbook(), output)
            self.assertEqual(output.read_bytes(), previous)

    def test_offline_command_uses_no_database_or_drive(self):
        inventory = synthetic(1, "MGA/Projeto/TABELA", "Tabela.pdf", "application/pdf")
        module = import_module("apps.robot.management.commands.mapear-fontes")
        with TemporaryDirectory() as directory:
            original, output = Path(directory) / "input.xlsx", Path(directory) / "output.xlsx"
            write_inventory(original, [inventory])
            with patch.object(module, "DriveSource") as database, patch.object(module, "drive_service", side_effect=AssertionError("must be offline")):
                database.objects.filter.side_effect = AssertionError("must be offline")
                call_command("mapear-filtros", input_inventory=original, output=output, stdout=StringIO())
            self.assertTrue(output.exists())
            self.assertEqual(len(read_inventory(original)[0][2]), 1)

    def test_human_metrics_require_labels_and_return_confusion_matrix(self):
        inventories = [synthetic(1, "MGA/Projeto/IMAGENS", "fachada.jpg")]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            write_sample(path, inventories)
            with self.assertRaises(ValueError):
                evaluate_sample(path)
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                headers, rows = reader.fieldnames, list(reader)
            rows[0]["categoria_humana"] = "fachada"
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
            result = evaluate_sample(path)
            self.assertEqual(result["labelled"], 1)
            self.assertEqual(result["per_category"]["fachada"]["f1"], 1)

    def test_transient_drive_errors_are_retried_and_credentials_are_sanitized(self):
        from googleapiclient.errors import HttpError
        from .drive import DriveAccessError, execute

        response = SimpleNamespace(status=503, reason="Unavailable")
        error = HttpError(response, b'{"error":{"message":"secret-token"}}')
        request = Mock()
        request.execute.side_effect = [error, {"files": []}]
        with patch("apps.robot.drive.sleep") as sleep:
            self.assertEqual(execute(request), {"files": []})
            sleep.assert_called_once_with(1)
        request.execute.side_effect = [error, error, error]
        with patch("apps.robot.drive.sleep"):
            with self.assertRaises(DriveAccessError) as caught:
                execute(request)
        self.assertNotIn("secret-token", str(caught.exception))

    def test_snapshot_replay_and_final_execution_duration(self):
        from .audit_report import finalize_execution_audit
        from .inventory import read_rule_snapshot

        inventory = synthetic(1, "MGA/Projeto/Imagens", "Fachada.jpg")
        with TemporaryDirectory() as directory:
            output = Path(directory) / "report.xlsx"
            write_filter_report(output, [inventory], {"errors": [], "started_at": "2026-11-24T21:00:00-03:00", "finished_at": "before", "duration_seconds": 1})
            finalize_execution_audit(output, {"finished_at": "2026-11-24T21:00:28-03:00", "duration_seconds": 28.3, "success": True})
            self.assertEqual(read_rule_snapshot(output)[inventory[0].pasta_id], get_profile(inventory[0]).config)
            book = load_workbook(output)
            audit = dict(book["Auditoria"].iter_rows(min_row=2, values_only=True))
            self.assertEqual(audit["duration_seconds"], 28.3)
            self.assertTrue(audit["success"])
            self.assertEqual(book["Arquivos"]["C2"].value, "Fachada.jpg")
            book.close()

    def test_comparison_uses_ids_and_matches_full_universe(self):
        from .comparison import compare

        inventory = synthetic(1, "MGA/Projeto/Imagens", "Fachada.jpg")
        with TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.xlsx"
            write_inventory(baseline, [inventory])
            # Mesmo ID/nova grafia não é um novo arquivo.
            inventory[2][0]["name"] = "Fachada NOVA.jpg"
            result = compare(baseline, [inventory])
            self.assertIn(("Recuperados", 0, 0), result["metrics"])
            inventory[2][0]["id"] = "different-id"
            with self.assertRaises(ValueError):
                compare(baseline, [inventory])

    def test_full_inventory_replay_preserves_checksums_and_duplicate_display_names(self):
        inventories = [synthetic(1, "MGA/Projeto/Imagens", "Fachada.jpg"), synthetic(10, "Elevare/Imagens", "Fachada.jpg")]
        for _, _, files in inventories:
            files[0].update(md5_checksum="abc123", image_metadata={"width": 1920, "height": 1080})
        with TemporaryDirectory() as directory:
            path = Path(directory) / "full.xlsx"
            write_inventory(path, inventories)
            loaded = read_inventory(path)
            self.assertEqual(len(loaded), 2)
            for _, _, files in loaded:
                self.assertEqual(files[0]["md5_checksum"], "abc123")
                self.assertEqual(files[0]["image_metadata"]["width"], 1920)


class SourceResilienceTests(TestCase):
    def test_v2_migration_preserves_custom_rules_and_is_idempotent(self):
        from django.apps import apps
        from django.db import connection

        source = DriveSource.objects.first()
        source.perfil["thresholds"] = {"category": 99, "project": 88, "developer": 88}
        source.perfil["categories"]["tabela_precos"]["enabled"] = False
        source.save()
        migration = import_module("apps.robot.migrations.0005_upgrade_filter_profiles_v2")
        migration.upgrade_profiles(apps, SimpleNamespace(connection=connection))
        migration.upgrade_profiles(apps, SimpleNamespace(connection=connection))
        source.refresh_from_db()
        self.assertEqual(source.perfil["thresholds"]["category"], 99)
        self.assertFalse(source.perfil["categories"]["tabela_precos"]["enabled"])

    def test_one_source_failure_does_not_interrupt_other_source(self):
        DriveSource.objects.update(ativa=False)
        bad = DriveSource.objects.create(nome="A inacessível", pasta_id="bad", perfil=PROFILES[2])
        good = DriveSource.objects.create(nome="B disponível", pasta_id="good", perfil=PROFILES[2])
        module = import_module("apps.robot.management.commands.mapear-fontes")
        from .drive import scan_source

        def scan(service, source):
            if source.pk == bad.pk:
                raise RuntimeError("secret credentials must not appear")
            return scan_source(service, source)

        with TemporaryDirectory() as directory:
            output = Path(directory) / "partial.xlsx"
            stderr = StringIO()
            with patch.object(module, "drive_service", return_value=FakeDrive()), patch.object(module, "scan_source", side_effect=scan):
                call_command("mapear-filtros", output=output, stdout=StringIO(), stderr=stderr)
            self.assertTrue(output.exists())
            self.assertIn("EXECUÇÃO PARCIAL", stderr.getvalue())
            self.assertNotIn("secret credentials", stderr.getvalue())
            book = load_workbook(output)
            audit = dict(book["Auditoria"].iter_rows(min_row=2, values_only=True))
            self.assertTrue(audit["partial"])
            book.close()
            with patch.object(module, "drive_service", return_value=FakeDrive()), patch.object(module, "scan_source", side_effect=scan):
                with self.assertRaises(CommandError):
                    call_command("mapear-filtros", output=Path(directory) / "strict.xlsx", strict=True, stdout=StringIO(), stderr=StringIO())
