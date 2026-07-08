from rest_framework import serializers

from .models import Banner


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ["id", "titulo", "subtitulo", "imagem", "botao_texto", "botao_link", "ativo", "ordem"]
        read_only_fields = ["id"]
