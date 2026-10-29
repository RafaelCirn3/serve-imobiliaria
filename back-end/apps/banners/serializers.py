from rest_framework import serializers

from .models import Banner


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ["id", "titulo", "subtitulo", "imagem", "botao_texto", "botao_link", "ativo", "ordem"]
        read_only_fields = ["id"]

from .home_content import HomeContent


class HomeContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeContent
        exclude = ["id"]

from .property_carousel import PropertyCarousel
from apps.properties.serializers import PublicPropertySerializer
from apps.properties.models import Property


class AdminPropertyCarouselSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyCarousel
        fields = ["id", "titulo", "subtitulo", "imoveis", "ativo", "ordem"]


class PublicPropertyCarouselSerializer(serializers.ModelSerializer):
    properties = serializers.SerializerMethodField()

    def get_properties(self, obj):
        queryset = obj.imoveis.filter(status=Property.Status.PUBLICADO).prefetch_related("imagens")
        return PublicPropertySerializer(queryset, many=True, context=self.context).data

    class Meta:
        model = PropertyCarousel
        fields = ["id", "titulo", "subtitulo", "properties", "ativo", "ordem"]
