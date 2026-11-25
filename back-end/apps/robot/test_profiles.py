from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase

from .drive import FOLDER_MIME, scan_source
from .models import DriveProject, DriveSource
from .profile_defaults import COMPANIES, DEFAULT_PROFILES, PROFILES, upgrade_profile
from .profiles import SourceProfile, normalize, project_name
from .sources import DEFAULT_SOURCES
from .sync import sync_sources
from .tests import FakeDrive


def asset(path, name, mime="image/jpeg"):
    return {"folder_path": path, "name": name, "mime_type": mime}


class ProfileTests(SimpleTestCase):
    def test_normalization_and_project_names(self):
        self.assertEqual(normalize("Cópia de 1- FACHADA_DIURNA.jpg"), "fachada diurna")
        self.assertEqual(project_name("2026.06 - Raveo (230 und)"), "Raveo")
        self.assertEqual(project_name("Elevare: Tabela | Book | Imagens & Plantas"), "Elevare")

    def test_all_profiles_and_companies_are_registered(self):
        self.assertEqual(len(DEFAULT_PROFILES), 16)
        self.assertEqual(len(COMPANIES), 13)
        keys = {company.key for company in COMPANIES}
        for config in PROFILES:
            self.assertTrue(set(config["related_companies"]) <= keys)

    def test_mixed_catalogs_do_not_infer_company_from_source(self):
        for index in (5, 7, 9):
            self.assertEqual(SourceProfile(PROFILES[index]).identity("Sem evidência").companies, ())
        self.assertEqual(SourceProfile(PROFILES[5]).identity("Mondo").companies, ("mga",))
        for index in (4, 12, 13):
            self.assertIn(SourceProfile(PROFILES[index]).identity("Desconhecido").confidence, ("nao_identificada", "nao_resolvida"))

    def test_canonical_elevare_and_distinct_holanda_projects(self):
        identities = [SourceProfile(PROFILES[i]).identity("Elevare: Tabela | Book") for i in (1, 7, 10)]
        self.assertEqual(len({i.key for i in identities}), 1)
        tambau, bessa = [SourceProfile(PROFILES[i]).identity("raiz") for i in (14, 15)]
        self.assertEqual(tambau.companies, bessa.companies)
        self.assertNotEqual(tambau.key, bessa.key)

    def test_mime_and_exclusions_prevent_false_positive(self):
        profile = SourceProfile(PROFILES[2])
        result = profile.classify(asset("ARC/MATERIAIS DA FACHADA", "fachada.pdf", "application/pdf"))
        self.assertIsNone(result["categoria"])
        result = profile.classify(asset("ARC/PLANTAS", "piscina.jpg"))
        self.assertTrue(result["excluido"])
        result = profile.classify(asset("ARC/IMAGENS", "fachada.jpg"))
        self.assertEqual(result["categoria"], "fachada")

    def test_unequivocal_parent_classifies_generic_heif(self):
        result = SourceProfile(PROFILES[8]).classify(asset("TF/1. Lançamentos/TF Breezy/1. FACHADA", "UUID.heif", "image/heif"))
        self.assertEqual(result["categoria"], "fachada")
        self.assertFalse(result["revisao"])
        result = SourceProfile(PROFILES[9]).classify(asset("BRASCON/ARPOAR", "INTERNA BRINQUEDOTECA.jpg"))
        self.assertEqual(result["categoria"], "lazer")

    def test_promotional_tables_and_mime_without_extension(self):
        result = SourceProfile(PROFILES[3]).classify(asset("DRX/BLACK DRX - 2026/HYDE PARK", "Tabela promocional", "application/pdf"))
        self.assertEqual(result["categoria"], "tabela_precos")
        self.assertEqual(result["versao_comercial"], "promocional")
        self.assertTrue(result["validar_atualidade"])

    def test_commercial_only_and_complementary_media(self):
        result = SourceProfile(PROFILES[13]).classify(asset("Avulsos", "fachada.jpg"))
        self.assertIsNone(result["categoria"])
        result = SourceProfile(PROFILES[12]).classify(asset("Externas", "EXTERNAS R00_03.jpg"))
        self.assertTrue(result["revisao"])

    def test_single_project_root_and_tf_second_level(self):
        for index, expected in ((2, {"root"}), (8, {"root", "photos"})):
            source = SimpleNamespace(pk=1, nome="Fonte", pasta_id=DEFAULT_SOURCES[index][1])
            _, files = scan_source(FakeDrive(), source)
            self.assertEqual({f["project_id"] for f in files}, expected)


class SavedProfileTests(TestCase):
    def test_migration_saves_all_filters(self):
        for source in DriveSource.objects.all():
            self.assertEqual(upgrade_profile(source.perfil), DEFAULT_PROFILES[source.pasta_id])

    def test_sync_links_same_project_across_sources_without_losing_origins(self):
        DriveSource.objects.update(ativa=False)
        for index in (1, 7, 10):
            source = DriveSource.objects.get(pasta_id=DEFAULT_SOURCES[index][1])
            source.ativa = True
            source.perfil = dict(source.perfil, project_name="Elevare", project_depth=0)
            source.save()
        self.assertEqual(sync_sources(FakeDrive()), {"criadas": 3, "atualizadas": 0})
        project = DriveProject.objects.get(chave="mga-tropical:elevare")
        self.assertEqual(project.origens.count(), 3)
        self.assertEqual(sync_sources(FakeDrive()), {"criadas": 0, "atualizadas": 0})
