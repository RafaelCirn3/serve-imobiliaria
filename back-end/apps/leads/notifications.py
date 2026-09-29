import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone

from .models import Lead

logger = logging.getLogger(__name__)


def notify_sale(lead_id):
    """Serialize notification attempts. Sent messages cannot be resent by retries."""
    with transaction.atomic():
        lead = Lead.objects.select_for_update().get(pk=lead_id)
        if lead.origem != Lead.Origem.VENDA_IMOVEL or lead.notificacao_status == "enviado":
            return lead
        lead.notificacao_tentativas += 1
        lead.notificacao_em = timezone.now()
        try:
            if not settings.SALE_EMAIL_ENABLED:
                raise ValueError("Email delivery is disabled")
            lines = ["Nova oferta de imóvel para venda", f"Protocolo: {lead.pk}",
                     f"Nome: {lead.nome}", f"E-mail: {lead.email}", f"Telefone: {lead.telefone}", ""]
            labels = {"tipo": "Tipo", "cep": "CEP", "cidade": "Cidade", "uf": "UF", "bairro": "Bairro",
                      "logradouro": "Rua", "numero": "Número", "complemento": "Complemento",
                      "quartos": "Quartos", "area_total": "Área total (m²)", "valor": "Valor pretendido (R$)"}
            lines.extend(f"{labels[key]}: {value}" for key, value in lead.dados_imovel.items()
                         if key in labels and value is not None and value != "")
            lines.extend(["", "Descrição:", lead.mensagem])
            message = EmailMessage(
                subject=f"SERVE — Oferta de imóvel #{lead.pk}", body="\n".join(lines),
                from_email=settings.DEFAULT_FROM_EMAIL, to=[settings.SALE_LEAD_RECIPIENT], reply_to=[lead.email],
            )
            if message.send(fail_silently=False) != 1:
                raise ValueError("Email was not accepted")
            lead.notificacao_status = "enviado"
        except Exception as error:
            lead.notificacao_status = "falhou"
            logger.warning("Sale notification failed: lead_id=%s error_type=%s", lead.pk, type(error).__name__)
        lead.save(update_fields=["notificacao_status", "notificacao_tentativas", "notificacao_em"])
        return lead
