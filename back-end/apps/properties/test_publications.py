from decimal import Decimal
from datetime import date
from unittest.mock import patch

from django.test import TestCase, SimpleTestCase
from rest_framework.test import APIClient

from .models import Property
from .publications import PublicationPolicy


class PricePolicyTests(SimpleTestCase):
    def test_floor_first_significant_digit_without_changing_exact_value(self):
        for value, expected in (("2122036", "2000000"), ("527286.81", "500000"),
                                ("999999.99", "900000"), ("1000000", "1000000"),
                                ("12000", "10000"), ("2.50", "2")):
            self.assertEqual(PublicationPolicy.starting_price(value), Decimal(expected))
        for value in (0, -1, "NaN", "Infinity"):
            with self.assertRaises(ValueError):
                PublicationPolicy.starting_price(value)


class GroupedPublicationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.a1 = self.unit("A", "101", "2600000")
        self.a2 = self.unit("A", "102", "2122036")
        self.b = self.unit("B", "101", "1800000")
        self.c = self.unit("C", "101", "3400000")
        self.draft = self.unit("A", "103", "1000000", status="rascunho")

    def unit(self, tower, unit, price, **changes):
        values = dict(titulo=f"Elevare {tower} {unit}", empreendimento="Elevare", construtora="MGA",
                      unidade=unit, torre=tower, valor=price, cidade="João Pessoa", bairro="Altiplano",
                      tipo="apartamento", finalidade="venda", status="publicado", descricao="Unidade específica",
                      agrupar_publicacao=True, quartos=3, suites=3, area_informada="141.41", andar="19")
        return Property.objects.create(**(values | changes))

    def test_three_towers_are_three_cards_with_minimum_public_price(self):
        data = self.client.get("/api/imoveis/").data
        self.assertEqual(data["count"], 3)
        group = next(p for p in data["results"] if p["torre"] == "A")
        self.assertEqual(group["titulo"], "Elevare — Torre A — 3 suítes — 141,41 m²")
        self.assertEqual(group["valor"], "2122036.00")
        self.assertEqual(group["valor_exibicao"], "2000000")
        self.assertEqual(group["quantidade_unidades"], 2)
        self.assertEqual(group["quartos"], 3)
        self.assertEqual(group["area_informada"], "141.41")
        self.a2.refresh_from_db()
        self.assertEqual(self.a2.valor, Decimal("2122036"))

    def test_detail_of_any_unit_resolves_group_and_exact_units_exclude_drafts(self):
        group = self.client.get(f"/api/imoveis/{self.a2.slug}/").data
        self.assertEqual(group["id"], self.a1.pk)
        units = self.client.get(f"/api/imoveis/{self.a2.slug}/unidades/").data
        self.assertEqual(len(units), 2)
        self.assertTrue(all("unidade" not in u and "andar" not in u for u in units))
        self.assertNotIn("unidade", group)
        self.assertNotIn("andar", group)
        self.assertNotIn("unidade", group["slug"])
        self.assertEqual(self.client.get(f"/api/imoveis/{group['slug']}/").status_code, 200)
        self.assertEqual(Decimal(units[0]["valor"]), Decimal("2122036"))
        self.assertEqual(self.client.get(f"/api/imoveis/{self.draft.slug}/").status_code, 404)

    def test_filter_matches_any_unit_not_only_representative(self):
        result = self.client.get("/api/imoveis/", {"valor_min": 2000000, "valor_max": 2200000, "quartos": 3}).data
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["torre"], "A")

    def test_unknown_tower_company_rental_and_avulsos_are_kept_separate(self):
        self.unit("", "201", "1200000")
        self.unit("A", "201", "1200000", construtora="Outra")
        self.unit("A", "202", "6000", finalidade="aluguel")
        avulso = self.unit("A", "203", "1500000", agrupar_publicacao=False)
        self.assertEqual(self.client.get("/api/imoveis/").data["count"], 7)
        detail = self.client.get(f"/api/imoveis/{avulso.slug}/").data
        self.assertFalse(detail["agrupado"])
        self.assertEqual(detail["valor_exibicao"], "1500000.00")

    def test_group_does_not_leak_draft_units_in_featured_or_map(self):
        self.a2.destaque = True
        self.a2.save()
        result = self.client.get("/api/imoveis/destaques/").data
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["quantidade_unidades"], 2)
        self.assertEqual(self.client.get("/api/imoveis/mapa/").data["count"], 3)

    def test_ordering_uses_group_minimum_instead_of_representative_price(self):
        self.unit("A", "104", "1500000")
        result = self.client.get("/api/imoveis/", {"ordering": "valor"}).data
        self.assertEqual([p["torre"] for p in result["results"]], ["A", "B", "C"])

    def test_same_tower_different_suites_or_area_gets_separate_publications(self):
        self.unit("A", "201", "2800000", quartos=4, suites=4, area_informada="191.16")
        self.unit("A", "301", "2900000", quartos=4, suites=4, area_informada="191.160")
        self.unit("A", "202", "2300000", area_informada="162.16")
        self.assertEqual(self.client.get("/api/imoveis/").data["count"], 5)

    def test_private_unit_and_floor_remain_in_admin_api(self):
        from django.contrib.auth import get_user_model
        self.client.force_authenticate(get_user_model().objects.create_user(username="testadmin", is_staff=True))
        data = self.client.get(f"/api/admin/imoveis/{self.a1.pk}/").data
        self.assertEqual(data["unidade"], "101")
        self.assertEqual(data["andar"], "19")

    def test_future_delivery_is_under_construction_but_expired_date_is_not_ready(self):
        self.a1.previsao_entrega = "2031-12"
        self.a1.save()
        with patch("apps.properties.models.timezone.localdate", return_value=date(2026, 11, 25)):
            self.assertEqual(self.a1.situacao_obra, "em_construcao")
        with patch("apps.properties.models.timezone.localdate", return_value=date(2032, 1, 1)):
            self.assertEqual(self.a1.situacao_obra, "entrega_a_confirmar")
