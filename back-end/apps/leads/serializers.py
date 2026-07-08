from rest_framework import serializers

from .models import Lead


class PublicLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ["id", "imovel", "nome", "email", "telefone", "mensagem", "origem", "criado_em"]
        read_only_fields = ["id", "criado_em"]


class AdminLeadSerializer(serializers.ModelSerializer):
    imovel_titulo = serializers.CharField(source="imovel.titulo", read_only=True)

    class Meta:
        model = Lead
        fields = [
            "id",
            "imovel",
            "imovel_titulo",
            "nome",
            "email",
            "telefone",
            "mensagem",
            "origem",
            "status",
            "criado_em",
        ]
        read_only_fields = ["id", "criado_em"]
