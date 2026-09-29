from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "email", "origem", "status", "notificacao_status", "criado_em")
    readonly_fields = ("idempotency_key", "payload_hash", "notificacao_status", "notificacao_tentativas", "notificacao_em")
    list_filter = ("origem", "status", "criado_em")
    search_fields = ("nome", "email", "telefone", "mensagem")
