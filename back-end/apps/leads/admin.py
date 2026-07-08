from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "email", "origem", "status", "criado_em")
    list_filter = ("origem", "status", "criado_em")
    search_fields = ("nome", "email", "telefone", "mensagem")
