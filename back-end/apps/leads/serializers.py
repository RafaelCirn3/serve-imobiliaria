from rest_framework import serializers

from .models import Lead
from apps.properties.models import Property


class PublicLeadSerializer(serializers.ModelSerializer):
    origem = serializers.ChoiceField(choices=["formulario", "whatsapp", "botao_contato"], default="formulario")
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
            "dados_imovel",
            "notificacao_status",
            "notificacao_tentativas",
            "notificacao_em",
        ]
        read_only_fields = ["id", "criado_em", "dados_imovel", "notificacao_status", "notificacao_tentativas", "notificacao_em"]


class SaleLeadSerializer(serializers.Serializer):
    idempotency_key = serializers.UUIDField()
    nome = serializers.CharField(max_length=120)
    email = serializers.EmailField(max_length=254)
    telefone = serializers.RegexField(r"^(?=(?:\D*[0-9]){10,15}\D*$)[0-9\s()+-]{10,30}$", max_length=30)
    mensagem = serializers.CharField(max_length=5000)
    tipo = serializers.ChoiceField(choices=Property.Tipo.choices, required=False, allow_blank=True)
    cep = serializers.CharField(max_length=9, required=False, allow_blank=True)
    cidade = serializers.CharField(max_length=120, required=False, allow_blank=True)
    uf = serializers.CharField(max_length=2, required=False, allow_blank=True)
    bairro = serializers.CharField(max_length=120, required=False, allow_blank=True)
    logradouro = serializers.CharField(max_length=255, required=False, allow_blank=True)
    numero = serializers.CharField(max_length=30, required=False, allow_blank=True)
    complemento = serializers.CharField(max_length=120, required=False, allow_blank=True)
    quartos = serializers.IntegerField(min_value=0, max_value=32767, required=False, allow_null=True)
    area_total = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, allow_null=True)
    valor = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, required=False, allow_null=True)
    website = serializers.CharField(required=False, allow_blank=True, max_length=100, write_only=True)

    def validate_website(self, value):
        if value:
            raise serializers.ValidationError("Não foi possível registrar a solicitação.")
        return value

    def validate_cep(self, value):
        value = value.replace("-", "").strip()
        if value and (len(value) != 8 or not value.isascii() or not value.isdigit()):
            raise serializers.ValidationError("Informe um CEP com oito dígitos.")
        return value
