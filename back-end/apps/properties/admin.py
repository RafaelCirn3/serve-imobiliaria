from django.contrib import admin

from .models import Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "finalidade", "status", "cidade", "bairro", "valor", "destaque")
    list_filter = ("status", "tipo", "finalidade", "destaque", "cidade")
    search_fields = ("titulo", "descricao", "cidade", "bairro")
    prepopulated_fields = {"slug": ("titulo",)}
    inlines = [PropertyImageInline]


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("imovel", "legenda", "ordem", "imagem_capa")
    list_filter = ("imagem_capa",)
