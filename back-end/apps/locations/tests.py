from unittest.mock import patch
from urllib.error import URLError
from django.core.cache import cache
from rest_framework.test import APITestCase
from .services import LocationUnavailable, fetch_json
from apps.properties.models import Property


class PostalAddressTests(APITestCase):
    def setUp(self):
        cache.clear()

    @patch("apps.locations.services.fetch_json")
    def test_valid_cep_is_cached_and_can_have_missing_fields(self, fetch):
        fetch.return_value = {"cep": "58000-000", "localidade": "João Pessoa", "uf": "PB", "bairro": "", "logradouro": ""}
        for cep in ("58000000", "58000-000"):
            response = self.client.get("/api/localizacao/cep/", {"cep": cep})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["bairro"], "")
        self.assertEqual(fetch.call_count, 1)

    @patch("apps.locations.services.fetch_json")
    def test_invalid_cep_does_not_call_provider(self, fetch):
        self.assertEqual(self.client.get("/api/localizacao/cep/", {"cep": "abc"}).status_code, 400)
        fetch.assert_not_called()

    @patch("apps.locations.services.fetch_json", return_value={"cep": "58000-000"})
    def test_authenticated_requests_respect_address_limit(self, fetch):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user(username="postal-user")
        self.client.force_authenticate(user=user)
        for _ in range(60):
            response = self.client.get("/api/localizacao/cep/", {"cep": "58000000"})
            self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/localizacao/cep/", {"cep": "58000000"}).status_code, 429)

    @patch("apps.locations.services.fetch_json", return_value={"erro": True})
    def test_missing_cep_returns_not_found(self, fetch):
        self.assertEqual(self.client.get("/api/localizacao/cep/", {"cep": "99999999"}).status_code, 404)

    @patch("apps.locations.services.urlopen", side_effect=URLError("timeout"))
    def test_provider_failure_allows_manual_fallback(self, fetch):
        response = self.client.get("/api/localizacao/cep/", {"cep": "58000000"})
        self.assertEqual(response.status_code, 503)

    @patch("apps.locations.services.fetch_json", return_value=[])
    def test_street_search_validates_city_and_encodes_path(self, fetch):
        response = self.client.get("/api/localizacao/enderecos/", {"cidade": "joao pessoa", "logradouro": "Rua São João"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Jo%C3%A3o%20Pessoa/Rua%20S%C3%A3o%20Jo%C3%A3o/json/", fetch.call_args.args[0])
        self.assertEqual(self.client.get("/api/localizacao/enderecos/", {"cidade": "Recife", "logradouro": "Rua"}).status_code, 400)
        self.assertEqual(self.client.get("/api/localizacao/enderecos/", {"cidade": "Cabedelo", "logradouro": "ab"}).status_code, 400)

    @patch("apps.locations.services.fetch_json", return_value={"cep": "01001-000", "localidade": "São Paulo", "uf": "SP"})
    def test_outside_area_cep_is_returned_without_substituting_city(self, fetch):
        response = self.client.get("/api/localizacao/cep/", {"cep": "01001000"})
        self.assertEqual(response.data["localidade"], "São Paulo")


class LocationFilterTests(APITestCase):
    def setUp(self):
        cache.clear()
        for city, neighborhood, street, state in (
            ("Cabedelo", "Intermares", "Rua São João", "publicado"),
            ("Cabedelo", "  INTERMARES ", "Rua   Sao Joao", "publicado"),
            ("Cabedelo", "Centro", "Rua Oculta", "rascunho"),
            ("João Pessoa", "Bessa", "Rua da Praia", "publicado"),
            ("Bananeiras", "Centro", "Rua da Serra", "publicado"),
        ):
            Property.objects.create(titulo=f"{city} {neighborhood} {street}", descricao="Teste", tipo="flat", finalidade="venda",
                                    status=state, cidade=city, bairro=neighborhood, logradouro=street, valor=100000, cep="58000000")

    def test_neighborhoods_are_scoped_deduplicated_and_public(self):
        response = self.client.get("/api/localizacao/bairros/", {"cidade": "cabedelo"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0].strip().lower(), "intermares")
        response = self.client.get("/api/localizacao/bairros/", {"cidade": "Joao Pessoa"})
        self.assertEqual(response.data, ["Bessa"])
        response = self.client.get("/api/localizacao/bairros/", {"cidade": "Bananeiras"})
        self.assertEqual(response.data, ["Centro"])

    def test_streets_require_city_and_neighborhood(self):
        response = self.client.get("/api/localizacao/ruas/", {"cidade": "Cabedelo", "bairro": "INTERMARES"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        response = self.client.get("/api/localizacao/ruas/", {"cidade": "Cabedelo", "bairro": "Bessa"})
        self.assertEqual(response.data, [])
        response = self.client.get("/api/localizacao/ruas/", {"cidade": "Cabedelo"})
        self.assertEqual(response.status_code, 400)

    def test_normalized_location_filters_and_cep_combine(self):
        response = self.client.get("/api/imoveis/", {"cidade": "CABEdelo", "bairro": "intermares", "logradouro": "rua sao joao", "cep": "58000-000"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        response = self.client.get("/api/imoveis/", {"cidade": "Joao Pessoa", "logradouro": "Rua da Praia"})
        self.assertEqual(response.data["count"], 1)

    def test_catalogue_admin_rejects_outside_city(self):
        from django.contrib.auth import get_user_model
        admin = get_user_model().objects.create_user(username="location-admin", is_staff=True)
        self.client.force_authenticate(user=admin)
        response = self.client.post("/api/admin/imoveis/", {
            "titulo": "Fora da área", "descricao": "Teste", "tipo": "flat", "finalidade": "venda",
            "cidade": "Recife", "uf": "PE", "bairro": "Centro", "valor": 100000,
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("cidade", response.data)


class GeocodingTests(APITestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        cache.clear()
        self.admin = get_user_model().objects.create_user(username="geocode-admin", is_staff=True)
        self.payload = {"cidade": "Cabedelo", "logradouro": "Rua da Praia", "numero": "123"}

    def test_public_cannot_geocode(self):
        response = self.client.post("/api/localizacao/geocodificar/", self.payload, format="json")
        self.assertIn(response.status_code, [401, 403])

    @patch("apps.locations.services.fetch_json", return_value=[{"lat": "-7.12", "lon": "-34.87", "display_name": "Cabedelo"}])
    def test_geocoding_is_cached_and_remains_approximate(self, fetch):
        self.client.force_authenticate(user=self.admin)
        for _ in range(2):
            response = self.client.post("/api/localizacao/geocodificar/", self.payload, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.data["localizacao_exata"])
        self.assertEqual(fetch.call_count, 1)
        response = self.client.post("/api/localizacao/geocodificar/", self.payload | {"numero": "124"}, format="json")
        self.assertEqual(response.status_code, 429)

    @patch("apps.locations.services.fetch_json", return_value=[])
    def test_missing_location_can_be_set_manually(self, fetch):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/localizacao/geocodificar/", self.payload, format="json")
        self.assertEqual(response.status_code, 404)
