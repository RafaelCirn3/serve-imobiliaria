from rest_framework import serializers
from decimal import Decimal

from .models import Property, PropertyImage
from apps.locations.normalization import canonical_city, normalized
from .publications import PublicationGroups


class PublicationListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        items = list(data.all() if hasattr(data, "all") else data)
        self.context["publication_groups"] = PublicationGroups(items)
        return super().to_representation(items)


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["id", "imagem", "legenda", "ordem", "imagem_capa", "criado_em", "categoria", "vistoria_pendente"]
        read_only_fields = ["id", "criado_em", "categoria", "vistoria_pendente"]


class PublicUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ["torre", "tipo", "finalidade", "valor", "area_informada", "area_total",
                  "area_privativa", "quartos", "suites", "banheiros", "vagas"]


class PublicPropertySerializer(serializers.ModelSerializer):
    imagens = PropertyImageSerializer(many=True, read_only=True)
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    numero = serializers.SerializerMethodField()
    complemento = serializers.SerializerMethodField()
    endereco = serializers.SerializerMethodField()
    agrupado = serializers.SerializerMethodField()
    quantidade_unidades = serializers.SerializerMethodField()
    valor_exibicao = serializers.SerializerMethodField()

    def group_policy(self, obj):
        if "publication_groups" not in self.context:
            self.context["publication_groups"] = PublicationGroups([obj])
        return self.context["publication_groups"]

    def get_agrupado(self, obj):
        return bool(obj.grupo_publicacao)

    def get_quantidade_unidades(self, obj):
        return len(self.group_policy(obj).for_property(obj))

    def get_valor_exibicao(self, obj):
        # The policy sets the price after collecting the whole group.
        return str(obj.valor)

    def to_representation(self, instance):
        return self.group_policy(instance).apply(instance, super().to_representation(instance))

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
        list_serializer_class = PublicationListSerializer
        fields = [
            "agrupado", "quantidade_unidades", "valor_exibicao",
            "previsao_entrega", "situacao_obra",
            "empreendimento", "torre", "construtora", "origem_comercial", "medidas", "area_informada",
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
            "vagas_rotativas",
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
    area_informada = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"), required=False, allow_null=True)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7, min_value=-90, max_value=90, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7, min_value=-180, max_value=180, required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        data = getattr(self, "initial_data", {})
        grouped = data.get("agrupar_publicacao", getattr(self.instance, "agrupar_publicacao", False))
        status = data.get("status", getattr(self.instance, "status", "rascunho"))
        self.draft_location_optional = self.context.get("robot_draft") or (grouped and status == "rascunho")
        if self.draft_location_optional:
            for field in ("cidade", "bairro"):
                self.fields[field].allow_blank = True
                self.fields[field].required = False

    def validate(self, attrs):
        from apps.locations.addressing import AddressNormalizer
        if attrs.get("endereco") and not attrs.get("logradouro", getattr(self.instance, "logradouro", "")):
            source = {key: attrs.get(key, getattr(self.instance, key, "")) for key in
                      ("endereco", "logradouro", "numero", "complemento", "cidade", "bairro", "uf", "cep")}
            attrs.update(AddressNormalizer.parse(source))
        district = AddressNormalizer.district(attrs.get("bairro", ""), attrs.get("cidade", getattr(self.instance, "cidade", "")))
        if district:
            attrs["bairro"] = district
            attrs["cidade"] = attrs.get("cidade") or "João Pessoa"
        latitude = attrs.get("latitude", getattr(self.instance, "latitude", None))
        longitude = attrs.get("longitude", getattr(self.instance, "longitude", None))
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError({"latitude": "Informe latitude e longitude juntas, ou deixe ambas vazias."})
        city = attrs.get("cidade", getattr(self.instance, "cidade", ""))
        uf = attrs.get("uf", getattr(self.instance, "uf", "PB")).upper()
        canonical = canonical_city(city)
        state = attrs.get("status", getattr(self.instance, "status", "rascunho"))
        location_pending = self.draft_location_optional and state == "rascunho" and not city
        if (not canonical and not location_pending) or uf != "PB":
            raise serializers.ValidationError({"cidade": "Selecione João Pessoa, Cabedelo ou Bananeiras/PB."})
        attrs["cidade"] = canonical or ""
        attrs["uf"] = uf
        if state == "publicado" and not attrs.get("bairro", getattr(self.instance, "bairro", "")):
            raise serializers.ValidationError({"bairro": "Confirme o bairro antes de publicar."})
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
        if not region and attrs.get("bairro") and canonical:
            from apps.locations.models import Region
            match = Region.objects.filter(nome=attrs["bairro"], cidade=canonical, ativo=True).first()
            if match:
                attrs["regiao"] = match
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
            "agrupar_publicacao", "grupo_publicacao",
            "andar", "tipologia",
            "previsao_entrega", "situacao_obra", "registro_incorporacao",
            "empreendimento", "unidade", "torre", "construtora", "origem_comercial", "medidas", "area_informada",
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
            "vagas_rotativas",
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
        read_only_fields = ["id", "slug", "criado_em", "atualizado_em", "publicado_em", "grupo_publicacao"]


class MapPropertySerializer(PublicPropertySerializer):
    foto = serializers.SerializerMethodField()

    def get_foto(self, obj):
        images = list(obj.imagens.all())
        cover = next((image for image in images if image.imagem_capa), images[0] if images else None)
        if not cover:
            return None
        return self.context["request"].build_absolute_uri(cover.imagem.url)

    class Meta(PublicPropertySerializer.Meta):
        fields = ["id", "titulo", "slug", "valor", "valor_exibicao", "agrupado", "quantidade_unidades", "cidade", "bairro", "latitude", "longitude", "localizacao_exata", "foto"]
