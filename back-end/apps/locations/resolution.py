"""Resolve verified CEP and approximate coordinates once per address."""

from rest_framework.exceptions import APIException

from .addressing import AddressNormalizer
from .normalization import canonical_city
from .services import search_address, geocode_address
from .models import Region


class AddressResolver:
    def resolve(self, data):
        fields = AddressNormalizer.parse(data)
        warnings, evidence = [], {}
        if fields["cidade"] and fields["bairro"]:
            region = Region.objects.filter(cidade=fields["cidade"], nome=fields["bairro"], ativo=True).first()
            if region:
                fields["regiao"] = region.pk
        if not canonical_city(fields["cidade"]) or not fields["logradouro"]:
            return {"fields": fields, "warnings": ["ENDERECO_INSUFICIENTE"], "evidence": evidence}
        if not fields["cep"]:
            try:
                matches = [item for item in search_address(fields["cidade"], fields["logradouro"])
                           if canonical_city(item.get("localidade", "")) == fields["cidade"] and item.get("uf") == fields["uf"]
                           and AddressNormalizer.street_key(item.get("logradouro", "")) == AddressNormalizer.street_key(fields["logradouro"])
                           and (not fields["bairro"] or AddressNormalizer.district(item.get("bairro", ""), fields["cidade"]) == fields["bairro"]
                                or item.get("bairro") == fields["bairro"])]
                postal_codes = {item.get("cep", "").replace("-", "") for item in matches}
                postal_codes = {cep for cep in postal_codes if len(cep) == 8 and cep.isdigit()}
                if len(postal_codes) == 1:
                    fields["cep"] = postal_codes.pop()
                    evidence["postal"] = {"provider": "ViaCEP", "address": matches[0]}
                else:
                    warnings.append("CEP_AMBIGUO" if postal_codes else "CEP_NAO_ENCONTRADO")
            except APIException as exc:
                warnings.append("CEP_INDISPONIVEL")
                evidence["postal_error"] = type(exc).__name__
        if data.get("latitude") is not None and data.get("longitude") is not None:
            fields.update({key: str(data[key]) for key in ("latitude", "longitude")})
            fields["localizacao_exata"] = bool(data.get("localizacao_exata"))
        else:
            try:
                coordinates = geocode_address(fields)
                fields.update({key: coordinates[key] for key in ("latitude", "longitude", "localizacao_exata")})
                evidence["geocode"] = coordinates
            except APIException as exc:
                warnings.append("COORDENADAS_PENDENTES")
                evidence["geocode_error"] = type(exc).__name__
        return {"fields": fields, "warnings": warnings, "evidence": evidence}

    def apply(self, property):
        from django.db import transaction
        from apps.properties.models import Property

        source = {key: getattr(property, key) for key in
                  ("endereco", "logradouro", "numero", "complemento", "cidade", "bairro", "uf", "cep",
                   "latitude", "longitude", "localizacao_exata")}
        result = self.resolve(source)
        with transaction.atomic():
            current = Property.objects.select_for_update().get(pk=property.pk)
            updates = []
            for key, value in result["fields"].items():
                target = "regiao_id" if key == "regiao" else key
                # Do not overwrite a concurrent manual edit while a provider responds.
                if key in source and getattr(current, target) != source[key]:
                    continue
                if value != "" and value is not None:
                    setattr(current, target, value)
                    updates.append("regiao" if key == "regiao" else key)
            if updates:
                current.save(update_fields=set(updates) | {"atualizado_em"})
        return result
