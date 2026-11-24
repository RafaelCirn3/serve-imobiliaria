from django.contrib import admin

from .models import DrivePublication, DriveSource


@admin.register(DriveSource)
class DriveSourceAdmin(admin.ModelAdmin):
    list_display = ("nome", "pasta_id", "ativa", "ultima_consulta_em")
    list_filter = ("ativa",)
    search_fields = ("nome", "pasta_id")
    readonly_fields = ("ultima_consulta_em",)


@admin.register(DrivePublication)
class DrivePublicationAdmin(admin.ModelAdmin):
    list_display = ("titulo", "fonte", "status", "criada_em", "atualizada_em")
    list_filter = ("fonte", "status")
    search_fields = ("titulo", "caminho", "pasta_id")
    readonly_fields = ("fonte", "pasta_id", "titulo", "caminho", "url_pasta", "arquivos", "criada_em", "atualizada_em")
