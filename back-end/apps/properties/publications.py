"""Publications group verified units without losing their exact commercial data."""

from collections import defaultdict
from decimal import Decimal, ROUND_FLOOR
import hashlib

from apps.locations.normalization import normalized
from django.utils.text import slugify


class PublicationPolicy:
    @staticmethod
    def key(property):
        if not property.agrupar_publicacao or not property.empreendimento.strip() or not property.construtora.strip():
            return ""
        # Sale and rental offers, cities and towers must never share a price.
        identity = [normalized(getattr(property, name)) for name in
                    ("construtora", "empreendimento", "cidade", "torre", "finalidade", "tipo")]
        return hashlib.sha256("|".join(identity).encode()).hexdigest()

    @staticmethod
    def area(property):
        for field in ("area_privativa", "area_total", "area_informada"):
            value = getattr(property, field)
            if value is not None and Decimal(str(value)) > 0:
                return Decimal(str(value)), field
        return None, ""

    @staticmethod
    def title(property):
        title = property.empreendimento + (f" — Torre {property.torre}" if property.torre else "")
        if property.suites:
            title += f" — {property.suites} suítes"
        elif property.quartos:
            title += f" — {property.quartos} quartos"
        area, _ = PublicationPolicy.area(property)
        if area:
            title += f" — {format(area, '.2f').replace('.', ',')} m²"
        return title

    @staticmethod
    def group_title(members):
        representative = members[0]
        if len({(p.quartos, p.suites, PublicationPolicy.area(p)) for p in members}) == 1:
            return PublicationPolicy.title(representative)
        return representative.empreendimento + (f" — Torre {representative.torre}" if representative.torre else "")

    @staticmethod
    def slug(property, title=None):
        return slugify(title or PublicationPolicy.title(property))[:140] + "-" + property.grupo_publicacao

    @staticmethod
    def starting_price(value):
        value = Decimal(str(value))
        if not value.is_finite() or value <= 0:
            raise ValueError("Preço positivo obrigatório.")
        magnitude = Decimal(10) ** max(0, value.adjusted())
        return (value / magnitude).to_integral_value(rounding=ROUND_FLOOR) * magnitude


class PublicationGroups:
    """One cached query for the groups on a page, including only public units."""

    def __init__(self, properties):
        from .models import Property

        keys = {p.grupo_publicacao for p in properties if p.grupo_publicacao}
        self.members = defaultdict(list)
        if keys:
            for member in Property.objects.filter(grupo_publicacao__in=keys, status=Property.Status.PUBLICADO).order_by("id"):
                self.members[member.grupo_publicacao].append(member)

    def for_property(self, property):
        return self.members.get(property.grupo_publicacao, [property])

    def apply(self, property, data):
        members = self.for_property(property)
        grouped = bool(property.grupo_publicacao)
        priced = [p.valor for p in members if p.valor is not None and p.valor > 0]
        minimum = min(priced) if priced else None
        data.update(agrupado=grouped, quantidade_unidades=len(members),
                    valor_exibicao=str(PublicationPolicy.starting_price(minimum) if grouped else minimum)
                    if minimum is not None else None)
        if not grouped:
            return data
        representative = members[0]
        title = PublicationPolicy.group_title(members)
        data.update(id=representative.pk, slug=representative.slug,
                    titulo=title, valor=str(minimum) if minimum is not None else None)
        data["slug"] = PublicationPolicy.slug(property, title)
        if "unidade" in data:
            data["unidade"] = ""
        if "tipo" in data and len({p.tipo for p in members}) > 1:
            data["tipo"] = "lancamento"
        # Do not present one unit's dimensions or amenities as applying to all.
        for field in ("area_total", "area_privativa", "area_informada", "valor_condominio", "valor_iptu",
                      "quartos", "suites", "banheiros", "vagas", "vagas_rotativas", "mobiliado",
                      "aceita_financiamento", "possui_piscina", "possui_academia", "possui_elevador", "possui_area_gourmet"):
            if field in data and len({getattr(p, field) for p in members}) > 1:
                data[field] = 0 if field in ("quartos", "suites", "banheiros", "vagas") else False if isinstance(getattr(property, field), bool) else None
        if "descricao" in data:
            data["descricao"] = f"{data['titulo']}. Consulte as unidades disponíveis e as condições comerciais."
        data["vagas_min"] = min(p.vagas for p in members)
        data["vagas_max"] = max(p.vagas for p in members)
        return data
