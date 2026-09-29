from django.core.management.base import BaseCommand
from apps.leads.models import Lead
from apps.leads.notifications import notify_sale


class Command(BaseCommand):
    help = "Reenvia notificações de venda pendentes ou com falha."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)

    def handle(self, *args, **options):
        ids = list(Lead.objects.filter(origem="venda_imovel", notificacao_status__in=["pendente", "falhou"])
                   .order_by("criado_em").values_list("id", flat=True)[:max(0, options["limit"])])
        sent = sum(notify_sale(pk).notificacao_status == "enviado" for pk in ids)
        self.stdout.write(f"Processadas: {len(ids)}; enviadas: {sent}.")
