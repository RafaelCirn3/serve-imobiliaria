from rest_framework import serializers

from .models import Property, PropertyImage


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["id", "imagem", "legenda", "ordem", "imagem_capa", "criado_em"]
        read_only_fields = ["id", "criado_em"]


class PublicPropertySerializer(serializers.ModelSerializer):
    imagens = PropertyImageSerializer(many=True, read_only=True)

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
            "latitude",
            "longitude",
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

    def validate(self, attrs):
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
            "latitude",
            "longitude",
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
