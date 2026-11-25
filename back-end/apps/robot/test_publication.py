from unittest.mock import patch

from django.test import TestCase

from apps.properties.models import PropertyImage
from .extraction.service import stage_table, commit_unit
from .publication import MGAPublicationPolicy
from .test_mga import extracted


class AutomaticPublicationTests(TestCase):
    def setUp(self):
        document, _ = stage_table(extracted(), drive_file_id="approved-standard")
        self.unit = document.units.first()
        with patch("apps.robot.extraction.service.schedule_location"):
            self.property, _ = commit_unit(self.unit.pk, with_images=False)
        for index, category in enumerate(("fachada", "fachada", "lazer", "lazer", "internos", "internos")):
            PropertyImage.objects.create(imovel=self.property, imagem=f"imoveis/photo-{index}.jpg",
                                         ordem=index, imagem_capa=index == 0, categoria=category)
        self.storage = patch("django.core.files.storage.FileSystemStorage.exists", return_value=True)
        self.storage.start()
        self.addCleanup(self.storage.stop)
        self.policy = MGAPublicationPolicy()

    def test_complete_offer_is_published_with_audit_and_idempotence(self):
        result = self.policy.apply(self.property.pk)
        self.assertTrue(result["published"], result)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, "publicado")
        published_at = self.property.publicado_em
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.evidence["publication"]["policy"], self.policy.version)
        self.assertFalse(self.policy.apply(self.property.pk)["published"])
        self.property.refresh_from_db()
        self.assertEqual(self.property.publicado_em, published_at)

    def test_insufficient_photos_and_missing_area_remain_drafts(self):
        self.property.imagens.last().delete()
        self.property.area_informada = None
        self.property.area_total = None
        self.property.area_privativa = None
        self.property.save()
        result = self.policy.apply(self.property.pk)
        self.assertFalse(result["published"])
        self.assertIn("SEM_AREA", result["issues"])
        self.assertIn("QUANTIDADE_DE_FOTOS", result["issues"])

    def test_unreviewed_conflict_blocks_automatic_approval(self):
        self.unit.warnings = ["CONFLITO_TIPOLOGIA"]
        self.unit.save(update_fields=["warnings"])
        self.assertIn("CONFERENCIA_DA_TABELA_PENDENTE", self.policy.apply(self.property.pk)["issues"])

    def test_missing_file_blocks_approval(self):
        with patch("django.core.files.storage.FileSystemStorage.exists", return_value=False):
            self.assertIn("ARQUIVO_DE_IMAGEM_AUSENTE", self.policy.apply(self.property.pk)["issues"])

    def test_wrong_cover_or_order_blocks_approval(self):
        self.property.imagens.filter(ordem=0).update(categoria="internos")
        self.assertIn("ORDEM_DA_GALERIA", self.policy.apply(self.property.pk)["issues"])

    def test_manual_withdrawal_is_preserved(self):
        self.property.status = "inativo"
        self.property.save()
        self.assertEqual(self.policy.apply(self.property.pk)["decision"], "status_preservado")
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, "inativo")

    def test_import_callback_publishes_only_after_gallery_finishes(self):
        with patch("apps.robot.extraction.service.schedule_location"), \
                patch("apps.robot.gallery.attach_images") as gallery, \
                self.captureOnCommitCallbacks(execute=True):
            commit_unit(self.unit.pk)
        gallery.assert_called_once_with(self.unit.pk)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, "publicado")
