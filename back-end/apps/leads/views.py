from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from apps.common.permissions import IsAdminUserOnly

from .models import Lead
from .serializers import AdminLeadSerializer, PublicLeadSerializer


class PublicLeadViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Lead.objects.all()
    serializer_class = PublicLeadSerializer
    permission_classes = [AllowAny]


class AdminLeadViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Lead.objects.select_related("imovel").all()
    serializer_class = AdminLeadSerializer
    permission_classes = [IsAdminUserOnly]
    filterset_fields = ["status", "origem", "imovel"]
    search_fields = ["nome", "email", "telefone", "mensagem"]
    ordering_fields = ["criado_em", "status"]
