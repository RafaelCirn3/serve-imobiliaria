from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from django.test import override_settings

from .models import Property


class PropertyProfileTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_user(username="profile-admin", is_staff=True)
        cls.flat = cls.create_property(
            titulo="Flat Cabedelo", tipo="flat", cidade="Cabedelo", bairro="Intermares",
            valor="450000", quartos=2, area_privativa="65", area_total="90",
        )
        cls.create_property(titulo="Flat João Pessoa", tipo="flat", cidade="João Pessoa")
        cls.create_property(titulo="Flat outro bairro", tipo="flat", bairro="Centro")
        cls.create_property(titulo="Flat menor", tipo="flat", quartos=1, area_privativa="40")
        cls.create_property(titulo="Flat caro", tipo="flat", valor="900000")
        cls.create_property(titulo="Flat rascunho", tipo="flat", status="rascunho")
        cls.land = cls.create_property(
            titulo="Terreno Bananeiras", tipo="terreno", cidade="Bananeiras", bairro="Centro",
            area_privativa=None, area_total="400", quartos=0,
        )

    @staticmethod
    def create_property(**overrides):
        data = {
            "titulo": "Imóvel", "descricao": "Imóvel para teste de perfil", "tipo": "apartamento",
            "finalidade": "venda", "status": "publicado", "cidade": "Cabedelo",
            "bairro": "Intermares", "valor": "450000", "quartos": 2,
            "area_privativa": "65", "area_total": "90",
        }
        return Property.objects.create(**(data | overrides))

    def test_combined_profile_filters(self):
        filters = {
            "tipo": "flat", "cidade": "Cabedelo", "bairro": "Intermares", "quartos": 2,
            "valor_min": 400000, "valor_max": 500000, "area_min": 60, "area_max": 70,
            "area_total_min": 85, "area_total_max": 95,
        }
        for path in ("/api/imoveis/", "/api/imoveis/busca/?q=Flat"):
            with self.subTest(path=path):
                response = self.client.get(path, filters)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["count"], 1)
                self.assertEqual(response.data["results"][0]["id"], self.flat.id)

    def test_total_area_filter_includes_land_without_private_area(self):
        response = self.client.get("/api/imoveis/", {
            "tipo": "terreno", "cidade": "Bananeiras", "area_total_min": 350, "area_total_max": 450,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.land.id)

    def test_existing_private_area_filter_keeps_its_meaning(self):
        response = self.client.get("/api/imoveis/", {"tipo": "terreno", "area_min": 350})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_invalid_ranges_return_validation_errors(self):
        for minimum, maximum in (
            ("valor_min", "valor_max"), ("area_min", "area_max"),
            ("area_total_min", "area_total_max"),
        ):
            with self.subTest(minimum=minimum):
                response = self.client.get("/api/imoveis/", {minimum: 200, maximum: 100})
                self.assertEqual(response.status_code, 400)
                self.assertIn(maximum, response.data)

    def test_negative_filter_is_rejected(self):
        for field in ("valor_min", "area_min", "area_total_min", "quartos"):
            with self.subTest(field=field):
                response = self.client.get("/api/imoveis/", {field: -1})
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)

    def test_public_count_excludes_drafts_even_with_status_filter(self):
        response = self.client.get("/api/imoveis/")
        self.assertEqual(response.data["count"], 6)
        response = self.client.get("/api/imoveis/", {"status": "rascunho"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_admin_can_create_and_publish_flat(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/admin/imoveis/", {
            "titulo": "Novo flat", "descricao": "Oferta", "tipo": "flat", "finalidade": "venda",
            "status": "publicado", "cidade": "Cabedelo", "bairro": "Intermares",
            "valor": "500000", "area_privativa": "70",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["tipo"], "flat")
        self.client.force_authenticate(user=None)
        detail = self.client.get(f'/api/imoveis/{response.data["slug"]}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["tipo"], "flat")

    def test_existing_types_remain_valid_for_admin(self):
        self.client.force_authenticate(user=self.admin)
        for property_type in ("apartamento", "casa", "cobertura", "terreno", "comercial", "condominio"):
            with self.subTest(property_type=property_type):
                response = self.client.patch(f"/api/admin/imoveis/{self.flat.id}/", {"tipo": property_type})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["tipo"], property_type)


class PropertyMapTests(APITestCase):
    def setUp(self):
        self.points = []
        for index in range(15):
            self.points.append(PropertyProfileTests.create_property(
                titulo=f"Mapa {index}", latitude="-7.1234567", longitude="-34.8765432",
                numero="123", complemento="Apartamento 8", endereco="Rua da Praia, 123", logradouro="Rua da Praia",
            ))
        PropertyProfileTests.create_property(titulo="Sem coordenadas")
        PropertyProfileTests.create_property(titulo="Mapa rascunho", status="rascunho", latitude="-7.12", longitude="-34.87")

    def test_map_covers_multiple_pages_and_counts_missing_coordinates(self):
        listing = self.client.get("/api/imoveis/")
        self.assertEqual(len(listing.data["results"]), 12)
        response = self.client.get("/api/imoveis/mapa/", {"cidade": "Cabedelo", "page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 16)
        self.assertEqual(len(response.data["results"]), 15)
        self.assertEqual(response.data["sem_coordenadas"], 1)
        self.assertFalse(response.data["truncado"])

    @override_settings(MAP_RESULT_LIMIT=2)
    def test_map_limit_is_explicit(self):
        response = self.client.get("/api/imoveis/mapa/")
        self.assertEqual(len(response.data["results"]), 2)
        self.assertTrue(response.data["truncado"])
        self.assertEqual(response.data["geolocalizados"], 15)

    def test_approximate_location_hides_number_and_rounds_coordinates(self):
        response = self.client.get(f"/api/imoveis/{self.points[0].slug}/")
        self.assertEqual(response.data["latitude"], "-7.123")
        self.assertEqual(response.data["numero"], "")
        self.assertEqual(response.data["complemento"], "")
        self.assertNotIn("123", response.data["endereco"])
        self.points[0].localizacao_exata = True
        self.points[0].save()
        response = self.client.get(f"/api/imoveis/{self.points[0].slug}/")
        self.assertEqual(response.data["latitude"], "-7.1234567")
        self.assertEqual(response.data["numero"], "123")

    def test_coordinates_must_be_paired_and_valid(self):
        admin = get_user_model().objects.create_user(username="map-admin", is_staff=True)
        self.client.force_authenticate(user=admin)
        for fields in ({"latitude": 91}, {"longitude": 181}, {"latitude": None}):
            with self.subTest(fields=fields):
                response = self.client.patch(f"/api/admin/imoveis/{self.points[0].id}/", fields, format="json")
                self.assertEqual(response.status_code, 400)

    def test_map_and_list_apply_same_filters(self):
        response = self.client.get("/api/imoveis/mapa/", {"cidade": "Bananeiras"})
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_map_and_list_match_multiword_search(self):
        property = self.points[0]
        property.titulo = "Flat com varanda"
        property.save()
        filters = {"search": "Flat varanda", "cidade": "Cabedelo"}
        listing = self.client.get("/api/imoveis/", filters)
        markers = self.client.get("/api/imoveis/mapa/", filters)
        self.assertEqual(listing.data["count"], 1)
        self.assertEqual(markers.data["count"], listing.data["count"])
        self.assertEqual(markers.data["results"][0]["id"], listing.data["results"][0]["id"])


class PropertyUploadTests(APITestCase):
    def setUp(self):
        import tempfile
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.directory.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.admin = get_user_model().objects.create_user(username='upload-admin', is_staff=True)
        self.client.force_authenticate(user=self.admin)
        self.property = PropertyProfileTests.create_property()
        self.url = f'/api/admin/imoveis/{self.property.pk}/imagens/'

    def test_append_photos_set_cover_with_json_and_delete(self):
        from apps.leads.tests import OfferPhotoTests
        for _ in range(2):
            response = self.client.post(self.url, {'imagens': [OfferPhotoTests.photo()]}, format='multipart')
            self.assertEqual(response.status_code, 201, response.data)
        images = list(self.property.imagens.all())
        self.assertEqual(len(images), 2)
        self.assertLess(images[0].ordem, images[1].ordem)
        response = self.client.patch(f'{self.url}{images[1].pk}/', {'imagem_capa': True}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data['imagem_capa'])
        response = self.client.delete(f'{self.url}{images[0].pk}/')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.property.imagens.count(), 1)

    def test_invalid_batch_does_not_leave_partial_upload(self):
        from apps.leads.tests import OfferPhotoTests
        from django.core.files.uploadedfile import SimpleUploadedFile
        response = self.client.post(self.url, {'imagens': [OfferPhotoTests.photo(), SimpleUploadedFile('bad.png', b'bad')]}, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.property.imagens.count(), 0)

    def test_admin_heic_upload_and_bad_metadata(self):
        from apps.leads.tests import OfferPhotoTests
        response = self.client.post(self.url, {'imagens': [OfferPhotoTests.photo('iphone.heic', format='HEIF')]}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(response.data[0]['imagem'].endswith('.jpg'))
        response = self.client.post(self.url, {'imagens': [OfferPhotoTests.photo()], 'ordem': -1}, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.property.imagens.count(), 1)


class AdminSummaryTests(APITestCase):
    def test_summary_counts_entire_catalog_and_distinct_properties(self):
        from apps.leads.models import Lead
        from .models import PropertyImage
        admin = get_user_model().objects.create_user(username='summary-admin', is_staff=True)
        for i in range(13):
            property = PropertyProfileTests.create_property(titulo=f'Imóvel {i}', status='publicado' if i == 0 else 'rascunho')
            if i == 0:
                for image in range(2):
                    PropertyImage.objects.create(imovel=property, imagem=f'imoveis/{image}.jpg')
        Lead.objects.create(nome='Contato', email='test@example.test', telefone='83999999999')
        self.client.force_authenticate(user=admin)
        response = self.client.get('/api/admin/imoveis/resumo/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'total': 13, 'publicados': 1, 'rascunhos': 12, 'sem_fotos': 12, 'leads': 1})

    def test_summary_is_admin_only(self):
        self.assertIn(self.client.get('/api/admin/imoveis/resumo/').status_code, [401,403])
        self.client.force_authenticate(user=get_user_model().objects.create_user(username='not-staff'))
        self.assertEqual(self.client.get('/api/admin/imoveis/resumo/').status_code, 403)

    def test_media_audit_reports_missing_file_without_deleting_record(self):
        import json
        from io import StringIO
        from django.core.management import call_command
        from .models import PropertyImage
        property = PropertyProfileTests.create_property()
        image = PropertyImage.objects.create(imovel=property, imagem='imoveis/missing-for-audit.jpg')
        output = StringIO()
        call_command('verificar_imagens', '--json', stdout=output)
        report = json.loads(output.getvalue())
        self.assertEqual(report['verificados'], 1)
        self.assertEqual(report['ausentes'][0]['id'], image.pk)
        self.assertTrue(PropertyImage.objects.filter(pk=image.pk).exists())
