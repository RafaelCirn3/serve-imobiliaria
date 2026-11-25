from rest_framework import serializers

from .models import Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "nome", "cidade", "descricao", "imagem", "ativo"]
        read_only_fields = ["id"]


class AddressOrganizationSerializer(serializers.Serializer):
    endereco = serializers.CharField(required=False, allow_blank=True, max_length=255)
    logradouro = serializers.CharField(required=False, allow_blank=True, max_length=255)
    numero = serializers.CharField(required=False, allow_blank=True, max_length=30)
    complemento = serializers.CharField(required=False, allow_blank=True, max_length=120)
    cidade = serializers.CharField(required=False, allow_blank=True, max_length=120)
    bairro = serializers.CharField(required=False, allow_blank=True, max_length=120)
    uf = serializers.CharField(required=False, allow_blank=True, max_length=2)
    cep = serializers.CharField(required=False, allow_blank=True, max_length=9)
    latitude = serializers.DecimalField(required=False, allow_null=True, max_digits=10, decimal_places=7, min_value=-90, max_value=90)
    longitude = serializers.DecimalField(required=False, allow_null=True, max_digits=10, decimal_places=7, min_value=-180, max_value=180)
    localizacao_exata = serializers.BooleanField(required=False, default=False)
