from django.contrib import admin

from .models import DriveProject, DrivePublication, DriveSource
from .models import TableImport, TableUnit


@admin.register(TableImport)
class TableImportAdmin(admin.ModelAdmin):
    list_display = ("filename", "developer_profile", "parser_version", "created_at")
    readonly_fields = ("identity", "content_sha256", "source_folder_id", "drive_file_id", "extraction", "context", "created_at")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(TableUnit)
class TableUnitAdmin(admin.ModelAdmin):
    list_display = ("id", "document", "index", "reviewed", "imported_property")
    readonly_fields = ("document", "index", "evidence", "warnings", "imported_property", "imported_at")
    actions = ["import_drafts"]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    @admin.action(description="Importar unidades válidas como rascunhos")
    def import_drafts(self, request, queryset):
        from rest_framework.exceptions import ValidationError
        from .extraction.service import commit_unit

        created = blocked = 0
        for unit in queryset:
            try:
                _, was_created = commit_unit(unit.pk)
                created += int(was_created)
            except ValidationError:
                blocked += 1
        self.message_user(request, f"{created} rascunho(s) criado(s); {blocked} unidade(s) requerem revisão.")


@admin.register(DriveProject)
class DriveProjectAdmin(admin.ModelAdmin):
    list_display = ("nome", "chave", "confianca")
    search_fields = ("nome", "chave")


@admin.register(DriveSource)
class DriveSourceAdmin(admin.ModelAdmin):
    list_display = ("nome", "pasta_id", "ativa", "ultima_consulta_em")
    list_filter = ("ativa",)
    search_fields = ("nome", "pasta_id")
    readonly_fields = ("ultima_consulta_em",)


@admin.register(DrivePublication)
class DrivePublicationAdmin(admin.ModelAdmin):
    list_display = ("titulo", "fonte", "empreendimento", "status", "criada_em", "atualizada_em")
    list_filter = ("fonte", "status")
    search_fields = ("titulo", "caminho", "pasta_id")
    readonly_fields = ("fonte", "pasta_id", "titulo", "caminho", "url_pasta", "arquivos", "criada_em", "atualizada_em")
