from rest_framework import serializers

from .models import Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "nome", "cidade", "descricao", "imagem", "ativo"]
        read_only_fields = ["id"]
