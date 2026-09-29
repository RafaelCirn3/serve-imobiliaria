from rest_framework import serializers

from .models import Property, PropertyImage
from apps.locations.normalization import canonical_city, normalized


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["id", "imagem", "legenda", "ordem", "imagem_capa", "criado_em"]
        read_only_fields = ["id", "criado_em"]


class PublicPropertySerializer(serializers.ModelSerializer):
    imagens = PropertyImageSerializer(many=True, read_only=True)
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    numero = serializers.SerializerMethodField()
    complemento = serializers.SerializerMethodField()
    endereco = serializers.SerializerMethodField()

    def get_latitude(self, obj):
        return self.coordinate(obj.latitude, obj.localizacao_exata)

    def get_longitude(self, obj):
        return self.coordinate(obj.longitude, obj.localizacao_exata)

    @staticmethod
    def coordinate(value, exact):
        if value is None:
            return None
        return str(value) if exact else f"{value:.3f}"

    def get_numero(self, obj):
        return obj.numero if obj.localizacao_exata else ""

    def get_complemento(self, obj):
        return obj.complemento if obj.localizacao_exata else ""

    def get_endereco(self, obj):
        return obj.endereco if obj.localizacao_exata else obj.logradouro or obj.bairro

    class Meta:
        model = Property
        fields = [
            "id",
            "titulo",
            "slug",
            "descricao",
            "tipo",
            "finalidade",
            "destaque",
            "valor",
            "valor_condominio",
            "valor_iptu",
            "regiao",
            "cidade",
            "bairro",
            "endereco",
            "cep",
            "uf", "logradouro", "numero", "complemento",
            "latitude",
            "longitude",
            "localizacao_exata",
            "area_total",
            "area_privativa",
            "quartos",
            "suites",
            "banheiros",
            "vagas",
            "aceita_financiamento",
            "mobiliado",
            "possui_piscina",
            "possui_academia",
            "possui_elevador",
            "possui_area_gourmet",
            "descricao_seo",
            "titulo_seo",
            "publicado_em",
            "imagens",
        ]


class AdminPropertySerializer(serializers.ModelSerializer):
    imagens = PropertyImageSerializer(many=True, read_only=True)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7, min_value=-90, max_value=90, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7, min_value=-180, max_value=180, required=False, allow_null=True)

    def validate(self, attrs):
        latitude = attrs.get("latitude", getattr(self.instance, "latitude", None))
        longitude = attrs.get("longitude", getattr(self.instance, "longitude", None))
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError({"latitude": "Informe latitude e longitude juntas, ou deixe ambas vazias."})
        city = attrs.get("cidade", getattr(self.instance, "cidade", ""))
        uf = attrs.get("uf", getattr(self.instance, "uf", "PB")).upper()
        canonical = canonical_city(city)
        if not canonical or uf != "PB":
            raise serializers.ValidationError({"cidade": "Selecione João Pessoa, Cabedelo ou Bananeiras/PB."})
        attrs["cidade"] = canonical
        attrs["uf"] = uf
        for field in ("bairro", "logradouro"):
            if field in attrs:
                attrs[field] = " ".join(attrs[field].split())
        if "cep" in attrs:
            cep = attrs["cep"].replace("-", "").strip()
            if cep and (len(cep) != 8 or not cep.isascii() or not cep.isdigit()):
                raise serializers.ValidationError({"cep": "Informe um CEP com oito dígitos."})
            attrs["cep"] = cep
        region = attrs.get("regiao", getattr(self.instance, "regiao", None))
        if region and normalized(region.cidade) != normalized(canonical):
            raise serializers.ValidationError({"regiao": "A região deve pertencer à cidade selecionada."})
        finalidade = attrs.get("finalidade", getattr(self.instance, "finalidade", None))
        status = attrs.get("status", getattr(self.instance, "status", None))

        if finalidade == Property.Finalidade.VENDA and status == Property.Status.ALUGADO:
            raise serializers.ValidationError({"status": "Imóvel com finalidade de venda não pode ter status alugado."})
        if finalidade == Property.Finalidade.ALUGUEL and status == Property.Status.VENDIDO:
            raise serializers.ValidationError({"status": "Imóvel com finalidade de aluguel não pode ter status vendido."})

        return attrs

    class Meta:
        model = Property
        fields = [
            "id",
            "titulo",
            "slug",
            "descricao",
            "tipo",
            "finalidade",
            "status",
            "destaque",
            "valor",
            "valor_condominio",
            "valor_iptu",
            "regiao",
            "cidade",
            "bairro",
            "endereco",
            "cep",
            "uf", "logradouro", "numero", "complemento",
            "latitude",
            "longitude",
            "localizacao_exata",
            "area_total",
            "area_privativa",
            "quartos",
            "suites",
            "banheiros",
            "vagas",
            "aceita_financiamento",
            "mobiliado",
            "possui_piscina",
            "possui_academia",
            "possui_elevador",
            "possui_area_gourmet",
            "descricao_seo",
            "titulo_seo",
            "criado_em",
            "atualizado_em",
            "publicado_em",
            "imagens",
        ]
        read_only_fields = ["id", "slug", "criado_em", "atualizado_em", "publicado_em"]


class MapPropertySerializer(PublicPropertySerializer):
    foto = serializers.SerializerMethodField()

    def get_foto(self, obj):
        images = list(obj.imagens.all())
        cover = next((image for image in images if image.imagem_capa), images[0] if images else None)
        if not cover:
            return None
        return self.context["request"].build_absolute_uri(cover.imagem.url)

    class Meta(PublicPropertySerializer.Meta):
        fields = ["id", "titulo", "slug", "valor", "cidade", "bairro", "latitude", "longitude", "localizacao_exata", "foto"]
