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
