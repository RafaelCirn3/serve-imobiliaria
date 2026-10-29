from django.contrib import admin

from .models import Banner, HomeContent, PropertyCarousel, SectionImage


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("titulo", "ativo", "ordem")
    list_filter = ("ativo",)
    search_fields = ("titulo", "subtitulo")


@admin.register(HomeContent)
class HomeContentAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not HomeContent.objects.exists() and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PropertyCarousel)
class PropertyCarouselAdmin(admin.ModelAdmin):
    list_display = ("titulo", "ativo", "ordem")
    filter_horizontal = ("imoveis",)


@admin.register(SectionImage)
class SectionImageAdmin(admin.ModelAdmin):
    list_display = ("section", "caption", "active", "position")
    list_filter = ("section", "active")
