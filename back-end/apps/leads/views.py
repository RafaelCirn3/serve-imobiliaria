from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from apps.common.permissions import IsAdminUserOnly

from .models import Lead
from .serializers import AdminLeadSerializer, PublicLeadSerializer
import hashlib
import json
from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from .serializers import SaleLeadSerializer
from .notifications import notify_sale


class SaleLeadThrottle(AnonRateThrottle):
    scope = "sale_leads"
    rate = "5/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class PublicLeadViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Lead.objects.all()
    serializer_class = PublicLeadSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"], url_path="venda-imovel", throttle_classes=[SaleLeadThrottle])
    def sale(self, request):
        serializer = SaleLeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        key = data.pop("idempotency_key")
        data.pop("website", None)
        signature = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
        contact = {field: data.pop(field) for field in ("nome", "email", "telefone", "mensagem")}
        details = json.loads(json.dumps(data, default=str))
        with transaction.atomic():
            lead, created = Lead.objects.get_or_create(idempotency_key=key, defaults={
                **contact, "dados_imovel": details, "payload_hash": signature,
                "origem": Lead.Origem.VENDA_IMOVEL, "notificacao_status": "pendente",
            })
        if lead.payload_hash != signature:
            return Response({"detail": "Esta solicitação já foi registrada com outros dados."}, status=409)
        if created:
            lead = notify_sale(lead.pk)
        return Response({"id": lead.pk, "notificacao_status": lead.notificacao_status}, status=201 if created else 200)


class AdminLeadViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Lead.objects.select_related("imovel").all()
    serializer_class = AdminLeadSerializer
    permission_classes = [IsAdminUserOnly]
    filterset_fields = ["status", "origem", "imovel"]
    search_fields = ["nome", "email", "telefone", "mensagem"]
    ordering_fields = ["criado_em", "status"]

    @action(detail=True, methods=["post"], url_path="reenviar-notificacao")
    def retry_notification(self, request, pk=None):
        lead = self.get_object()
        if lead.origem != Lead.Origem.VENDA_IMOVEL:
            return Response({"detail": "Este lead não é uma oferta de venda."}, status=400)
        return Response(self.get_serializer(notify_sale(lead.pk)).data)
