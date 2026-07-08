from django.contrib import admin

from .models import Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("nome", "cidade", "ativo")
    list_filter = ("cidade", "ativo")
    search_fields = ("nome", "cidade", "descricao")
