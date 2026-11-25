from decimal import Decimal
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json

from django.core.cache import cache
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient
from apps.properties.models import Property
from apps.robot.models import TableImport, TableUnit
from .addressing import AddressNormalizer
from .resolution import AddressResolver
from .services import LocationUnavailable


ADDRESS = "Rua Josita Almeida, 373, Altiplano Cabo Branco"
POSTAL = {"cep":"58046-490", "logradouro":"Rua Josita Almeida", "bairro":"Altiplano Cabo Branco", "localidade":"João Pessoa", "uf":"PB"}


class AddressParsingTests(SimpleTestCase):
    def test_first_district_wins_and_city_is_inferred_without_number_guess(self):
        data = AddressNormalizer.parse({"endereco":ADDRESS})
        self.assertEqual((data["logradouro"],data["numero"],data["bairro"],data["cidade"]),
                         ("Rua Josita Almeida","373","Altiplano","João Pessoa"))
        self.assertEqual(data["endereco"],ADDRESS)
        self.assertEqual(AddressNormalizer.district("Cabo Branco / Altiplano"),"Cabo Branco")
        self.assertEqual(AddressNormalizer.district("Tambau - Cabo Branco"),"Tambaú")
        self.assertIsNone(AddressNormalizer.district("Cabo Branco", "Cabedelo"))
        self.assertEqual(AddressNormalizer.parse({"endereco":"Rua Desconhecida", "bairro":"Não identificado"})["cidade"], "")
        self.assertEqual(AddressNormalizer.parse({"endereco":"Rua Josita Almeida, Altiplano"})["numero"], "")


class AddressResolutionTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch("apps.locations.resolution.geocode_address")
    @patch("apps.locations.resolution.search_address", return_value=[POSTAL])
    def test_unique_cep_and_existing_exact_coordinates_are_preserved(self, postal, geo):
        result = AddressResolver().resolve({"endereco":ADDRESS, "latitude":Decimal('-7.1'),"longitude":Decimal('-34.8'),"localizacao_exata":True})
        self.assertEqual(result["fields"]["cep"],"58046490")
        self.assertEqual(result["fields"]["bairro"],"Altiplano")
        self.assertEqual(result["fields"]["latitude"],"-7.1")
        self.assertTrue(result["fields"]["localizacao_exata"])
        json.dumps(result)
        geo.assert_not_called()

    @patch("apps.locations.resolution.geocode_address", side_effect=LocationUnavailable())
    @patch("apps.locations.resolution.search_address", return_value=[POSTAL, {**POSTAL,"cep":"58046-380"}])
    def test_ambiguous_postal_code_is_not_chosen_and_failure_keeps_address(self, postal, geo):
        result = AddressResolver().resolve({"endereco":ADDRESS})
        self.assertEqual(result["fields"]["cep"],"")
        self.assertIn("CEP_AMBIGUO",result["warnings"])
        self.assertIn("COORDENADAS_PENDENTES",result["warnings"])
        self.assertEqual(result["fields"]["numero"],"373")

    @patch("apps.locations.services.fetch_json")
    def test_batch_reuses_provider_queries_and_fills_region_area_and_coordinates(self, fetch):
        fetch.side_effect=lambda url: [POSTAL] if 'viacep' in url else [{"lat":"-7.1383523","lon":"-34.8267168","display_name":"Rua Josita Almeida, João Pessoa"}]
        document = TableImport.objects.create(identity="address-test",content_sha256="hash",filename="Elevare.pdf",parser_version="test")
        properties=[]
        for index in (1,2):
            property=Property.objects.create(titulo=f"Elevare {index}",empreendimento="Elevare",unidade=str(index),descricao="Teste",tipo="apartamento",finalidade="venda",valor=2000000,endereco=ADDRESS,cidade="João Pessoa",bairro="Altiplano Cabo Branco",area_informada="141.41")
            TableUnit.objects.create(document=document,index=index,imported_property=property)
            properties.append(property)
        with TemporaryDirectory() as directory:
            options=dict(empreendimento="Elevare",aplicar=True,area_total=True,output=Path(directory)/"report.json",stdout=StringIO())
            call_command("organizar-enderecos",**options)
            for property in properties:
                property.refresh_from_db()
                self.assertEqual(property.numero,"373")
                self.assertEqual(property.cep,"58046490")
                self.assertEqual(property.bairro,"Altiplano")
                self.assertEqual(property.regiao.nome,"Altiplano")
                self.assertEqual(property.area_total,Decimal('141.41'))
                self.assertEqual(property.latitude,Decimal('-7.1383523'))
                self.assertFalse(property.localizacao_exata)
            call_command("organizar-enderecos",**options)
        self.assertEqual(fetch.call_count,2)

    def test_admin_only_endpoint_and_postal_response_preserve_primary_district(self):
        from django.contrib.auth import get_user_model
        client=APIClient()
        self.assertIn(client.post('/api/localizacao/organizar/',{'endereco':ADDRESS}).status_code,[401,403])
        client.force_authenticate(get_user_model().objects.create_user(username='organize-admin',is_staff=True))
        with patch('apps.locations.services.fetch_json',return_value=POSTAL):
            response=client.get('/api/localizacao/cep/',{'cep':'58046490'})
        self.assertEqual(response.data['bairro'],'Altiplano')
        self.assertEqual(response.data['bairro_original'],'Altiplano Cabo Branco')
