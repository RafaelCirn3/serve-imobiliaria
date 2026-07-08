from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LogoutView, ServeTokenObtainPairView
from apps.banners.views import AdminBannerViewSet, PublicBannerViewSet
from apps.leads.views import AdminLeadViewSet, PublicLeadViewSet
from apps.locations.views import AdminRegionViewSet, PublicRegionViewSet
from apps.properties.views import AdminPropertyViewSet, PublicPropertyViewSet

router = DefaultRouter()
router.register("imoveis", PublicPropertyViewSet, basename="public-imoveis")
router.register("leads", PublicLeadViewSet, basename="public-leads")
router.register("regioes", PublicRegionViewSet, basename="public-regioes")
router.register("banners", PublicBannerViewSet, basename="public-banners")
router.register("admin/imoveis", AdminPropertyViewSet, basename="admin-imoveis")
router.register("admin/leads", AdminLeadViewSet, basename="admin-leads")
router.register("admin/regioes", AdminRegionViewSet, basename="admin-regioes")
router.register("admin/banners", AdminBannerViewSet, basename="admin-banners")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login/", ServeTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/logout/", LogoutView.as_view(), name="token_logout"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
