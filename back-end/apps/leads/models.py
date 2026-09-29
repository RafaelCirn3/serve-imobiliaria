from django.db import models

from apps.properties.models import Property


class Lead(models.Model):
    class Origem(models.TextChoices):
        FORMULARIO = "formulario", "Formulario"
        WHATSAPP = "whatsapp", "WhatsApp"
        BOTAO_CONTATO = "botao_contato", "Botao de contato"
        VENDA_IMOVEL = "venda_imovel", "Venda de imóvel"

    class Status(models.TextChoices):
        NOVO = "novo", "Novo"
        EM_ATENDIMENTO = "em_atendimento", "Em atendimento"
        FINALIZADO = "finalizado", "Finalizado"
        DESCARTADO = "descartado", "Descartado"

    imovel = models.ForeignKey(Property, related_name="leads", on_delete=models.SET_NULL, null=True, blank=True)
    nome = models.CharField(max_length=120)
    email = models.EmailField()
    telefone = models.CharField(max_length=30)
    mensagem = models.TextField(blank=True)
    origem = models.CharField(max_length=30, choices=Origem.choices, default=Origem.FORMULARIO)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.NOVO)
    criado_em = models.DateTimeField(auto_now_add=True)
    dados_imovel = models.JSONField(default=dict, blank=True)
    idempotency_key = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    payload_hash = models.CharField(max_length=64, blank=True, editable=False)
    notificacao_status = models.CharField(max_length=20, default="nao_aplicavel", choices=[
        ("nao_aplicavel", "Não aplicável"), ("pendente", "Pendente"),
        ("enviado", "Enviado"), ("falhou", "Falhou"),
    ])
    notificacao_tentativas = models.PositiveIntegerField(default=0)
    notificacao_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.nome} - {self.telefone}"
