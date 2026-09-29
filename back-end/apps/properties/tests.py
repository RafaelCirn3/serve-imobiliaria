from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

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
