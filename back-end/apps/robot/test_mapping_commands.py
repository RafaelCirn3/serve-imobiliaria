from importlib import import_module
from io import StringIO
from itertools import count
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError
from django.test import TestCase
from openpyxl import load_workbook

from .models import DrivePublication, DriveSource
from .profile_defaults import PROFILES
from .tests import FakeDrive


class MappingCommandsTests(TestCase):
    def setUp(self):
        DriveSource.objects.update(ativa=False)
        self.source = DriveSource.objects.create(nome="Fonte teste", pasta_id="root", perfil=PROFILES[2])
        self.module = import_module("apps.robot.management.commands.mapear-fontes")

    def run_mapping(self, command, output, drive=None, **kwargs):
        with patch.object(self.module, "drive_service", return_value=drive or FakeDrive()):
            call_command(command, output=output, stdout=StringIO(), **kwargs)

    def test_complete_and_filtered_workbooks_have_different_materials_and_counts(self):
        drive = FakeDrive()
        drive.pages[("root", None)]["files"].append(
            {"id": "excluded", "name": "plantas fachada.jpg", "mimeType": "image/jpeg"}
        )
        with TemporaryDirectory() as directory:
            complete = Path(directory) / "complete.xlsx"
            filtered = Path(directory) / "filtered.xlsx"
            self.run_mapping("mapear-fontes", complete, drive)
            self.run_mapping("mapear-filtros", filtered, drive)
            for output, expected_names in (
                (complete, {"nota.txt", "plantas fachada.jpg", "fachada.jpg"}),
                (filtered, {"fachada.jpg"}),
            ):
                book = load_workbook(output)
                self.assertEqual({row[2] for row in book["Arquivos"].iter_rows(min_row=2, values_only=True)}, expected_names)
                self.assertEqual(book["Resumo"]["C2"].value, len(expected_names))
                book.close()
        self.assertFalse(DrivePublication.objects.exists())

    def test_filtered_mapping_keeps_review_flag_and_prunes_unused_folders(self):
        drive = FakeDrive()
        drive.pages[("photos", None)]["files"][0]["name"] = "living.jpg"
        drive.pages[("root", None)]["files"].append(
            {"id": "empty", "name": "Pasta vazia", "mimeType": "application/vnd.google-apps.folder"}
        )
        drive.pages[("empty", None)] = {"files": []}
        with TemporaryDirectory() as directory:
            output = Path(directory) / "filtered.xlsx"
            self.run_mapping("mapear-filtros", output, drive, source="root")
            book = load_workbook(output)
            self.assertEqual(book["Pastas"].max_row, 5)  # V2 audita também as pastas sem materiais selecionados.
            self.assertEqual(book["Arquivos"]["M2"].value, "internos")
            self.assertTrue(book["Arquivos"]["O2"].value)
            book.close()

    def test_missing_profile_selects_no_files_and_warns(self):
        self.source.perfil = {}
        self.source.save()
        stderr = StringIO()
        with TemporaryDirectory() as directory:
            output = Path(directory) / "filtered.xlsx"
            self.run_mapping("mapear-filtros", output, stderr=stderr)
            book = load_workbook(output)
            self.assertEqual(book["Arquivos"].max_row, 1)
            self.assertEqual(book["Pastas"].max_row, 4)  # Fonte sem perfil continua rastreável.
            self.assertIn("Fonte sem perfil", stderr.getvalue())
            book.close()

    def test_filtered_mapping_uses_default_profiles_without_database(self):
        from .sources import DEFAULT_SOURCES

        with TemporaryDirectory() as directory:
            output = Path(directory) / "filtered.xlsx"
            with patch.object(self.module, "DriveSource") as source:
                source.objects.filter.side_effect = OperationalError("unavailable")
                self.run_mapping("mapear-filtros", output, source=DEFAULT_SOURCES[2][1], stderr=StringIO())
            book = load_workbook(output)
            self.assertEqual(book["Arquivos"].max_row, 2)
            self.assertEqual(book["Arquivos"]["C2"].value, "fachada.jpg")
            book.close()

    def test_filtered_mapping_failure_does_not_write_partial_workbook(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "filtered.xlsx"
            with patch.object(self.module, "scan_source", side_effect=RuntimeError("Drive unavailable")):
                with self.assertRaises(CommandError):
                    self.run_mapping("mapear-filtros", output)
            self.assertFalse(output.exists())

    def test_both_commands_report_elapsed_time_and_milestones(self):
        with TemporaryDirectory() as directory:
            for command, preparation in (("mapear-fontes", "Organização do inventário completo"),
                                         ("mapear-filtros", "Aplicação dos filtros da fonte")):
                with self.subTest(command=command):
                    stdout = StringIO()
                    with patch.object(self.module, "drive_service", return_value=FakeDrive()), \
                         patch.object(self.module, "perf_counter", side_effect=count(0, 1)):
                        call_command(command, output=Path(directory) / f"{command}.xlsx", stdout=stdout)
                    log = stdout.getvalue()
                    milestones = ["Início do mapeamento", "Carregando fontes", "Conexão com o Google Drive preparada",
                                  "iniciando consulta", "consulta finalizada", preparation,
                                  "arquivo(s) no relatório", "Gravando planilha", "Planilha gravada", "Concluído"]
                    positions = [log.index(text) for text in milestones]
                    self.assertEqual(positions, sorted(positions))
                    self.assertIn("[00:00:01.0]", log)
                    self.assertIn("Fonte 1/1: Fonte teste (root)", log)
                    self.assertIn("tempo total de execução", log)
                    self.assertEqual(self.module.Command.format_duration(3661.2), "01:01:01.2")

    def test_error_reports_elapsed_time_without_success_message(self):
        stdout = StringIO()
        with TemporaryDirectory() as directory:
            with patch.object(self.module, "drive_service", return_value=FakeDrive()), \
                 patch.object(self.module, "scan_source", side_effect=RuntimeError("Drive unavailable")):
                with self.assertRaises(CommandError):
                    call_command("mapear-filtros", output=Path(directory) / "failed.xlsx", stdout=stdout)
        self.assertIn("Interrompido — tempo total de execução", stdout.getvalue())
        self.assertNotIn("Concluído", stdout.getvalue())

    def test_verbosity_zero_hides_progress(self):
        with TemporaryDirectory() as directory:
            stdout = StringIO()
            with patch.object(self.module, "drive_service", return_value=FakeDrive()):
                call_command("mapear-fontes", output=Path(directory) / "quiet.xlsx", stdout=stdout, verbosity=0)
            self.assertNotIn("tempo total", stdout.getvalue())
            self.assertNotIn("iniciando consulta", stdout.getvalue())
