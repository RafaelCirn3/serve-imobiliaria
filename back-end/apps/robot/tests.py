from pathlib import Path
from importlib import import_module
from io import StringIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.db import OperationalError
from django.test import SimpleTestCase, TestCase, override_settings
from openpyxl import load_workbook

from .drive import FOLDER_MIME, drive_service, scan_source
from .models import DrivePublication, DriveSource
from .sync import sync_sources


class FakeRequest:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class FakeDrive:
    def __init__(self):
        self.pages = {
            ("root", None): {"files": [{"id": "project", "name": "Residencial A", "mimeType": FOLDER_MIME}], "nextPageToken": "more"},
            ("root", "more"): {"files": [{"id": "top-file", "name": "nota.txt", "mimeType": "text/plain"}]},
            ("project", None): {"files": [{"id": "photos", "name": "Fotos", "mimeType": FOLDER_MIME}]},
            ("photos", None): {"files": [{"id": "photo-1", "name": "fachada.jpg", "mimeType": "image/jpeg", "size": "1200"}]},
        }

    def files(self):
        return self

    def get(self, **kwargs):
        return FakeRequest({"id": "root", "name": "Fonte A", "mimeType": FOLDER_MIME})

    def list(self, **kwargs):
        folder_id = kwargs["q"].split("'")[1]
        return FakeRequest(self.pages[(folder_id, kwargs.get("pageToken"))])


class DriveScanTests(SimpleTestCase):
    @override_settings(GOOGLE_DRIVE_CREDENTIALS_JSON="", GOOGLE_DRIVE_CREDENTIALS_FILE="", GOOGLE_DRIVE_API_KEY="test-public-key")
    @patch("googleapiclient.discovery.build")
    def test_api_key_is_used_for_public_folders(self, build):
        drive_service()
        self.assertEqual(build.call_args.kwargs["developerKey"], "test-public-key")

    def test_scans_every_page_and_nested_folder(self):
        source = SimpleNamespace(pk=1, nome="Fonte A", pasta_id="root")
        folders, files = scan_source(FakeDrive(), source)
        self.assertEqual({item["id"] for item in folders}, {"root", "project", "photos"})
        self.assertEqual({item["id"] for item in files}, {"top-file", "photo-1"})
        photo = next(item for item in files if item["id"] == "photo-1")
        self.assertEqual(photo["project_id"], "project")
        self.assertEqual(photo["folder_path"], "Fonte A/Residencial A/Fotos")


class DriveSyncTests(TestCase):
    def setUp(self):
        DriveSource.objects.exclude(pasta_id="root").update(ativa=False)
        self.source = DriveSource.objects.create(nome="Fonte A", pasta_id="root")

    def test_sync_creates_pending_divulgations_and_is_idempotent(self):
        self.assertEqual(sync_sources(FakeDrive()), {"criadas": 2, "atualizadas": 0})
        self.assertEqual(sync_sources(FakeDrive()), {"criadas": 0, "atualizadas": 0})
        self.assertEqual(DrivePublication.objects.count(), 2)
        publication = DrivePublication.objects.get(pasta_id="project")
        self.assertEqual(publication.status, DrivePublication.Status.PENDENTE)
        self.assertEqual(publication.arquivos[0]["nome"], "fachada.jpg")
        publication.status = DrivePublication.Status.REVISADA
        publication.save()
        changed = FakeDrive()
        changed.pages[("photos", None)]["files"][0]["name"] = "fachada nova.jpg"
        self.assertEqual(sync_sources(changed), {"criadas": 0, "atualizadas": 1})
        publication.refresh_from_db()
        self.assertEqual(publication.status, DrivePublication.Status.REVISADA)

    def test_manual_command_generates_complete_workbook(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "fontes.xlsx"
            command_module = import_module("apps.robot.management.commands.mapear-fontes")
            with patch.object(command_module, "drive_service", return_value=FakeDrive()):
                call_command("mapear-fontes", output=output)
            book = load_workbook(output)
            self.assertEqual(book.sheetnames, ["Resumo", "Fontes", "Pastas", "Arquivos"])
            self.assertEqual(book["Resumo"]["C2"].value, 2)
            self.assertEqual(book["Pastas"].max_row, 4)
            self.assertEqual(book["Arquivos"].max_row, 3)
            self.assertIsNotNone(book["Arquivos"]["I2"].hyperlink)

    def test_manual_command_uses_initial_sources_when_database_is_unavailable(self):
        command_module = import_module("apps.robot.management.commands.mapear-fontes")
        stderr = StringIO()
        with TemporaryDirectory() as directory:
            output = Path(directory) / "fontes.xlsx"
            with patch.object(command_module, "DriveSource") as mocked_source, \
                 patch.object(command_module, "drive_service", return_value=FakeDrive()), \
                 patch.object(command_module, "scan_source", return_value=([], [])) as scan:
                mocked_source.objects.filter.side_effect = OperationalError("bad password")
                call_command("mapear-fontes", output=output, stderr=stderr)
            self.assertEqual(scan.call_count, 2)
            self.assertIn("usando as duas fontes padrão", stderr.getvalue())
            book = load_workbook(output)
            self.assertEqual(book["Fontes"].max_row, 3)
