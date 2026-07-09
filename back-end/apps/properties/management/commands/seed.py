from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.banners.models import Banner
from apps.locations.models import Region
from apps.properties.models import Property


class Command(BaseCommand):
    help = "Cria usuario admin e dados iniciais para desenvolvimento."

    def handle(self, *args, **options):
        User = get_user_model()
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@serve.local",
                "first_name": "Administrador",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Admin criado: admin / admin123"))
        else:
            self.stdout.write("Admin ja existe.")

        bessa, _ = Region.objects.get_or_create(
            nome="Bessa",
            cidade="João Pessoa",
            defaults={"descricao": "Região valorizada, próxima à praia e serviços.", "ativo": True},
        )
        altiplano, _ = Region.objects.get_or_create(
            nome="Altiplano",
            cidade="João Pessoa",
            defaults={"descricao": "Bairro verticalizado, com condomínios modernos.", "ativo": True},
        )

        Property.objects.get_or_create(
            titulo="Apartamento no Bessa com varanda",
            defaults={
                "descricao": "Apartamento publicado para demonstração da API.",
                "tipo": Property.Tipo.APARTAMENTO,
                "finalidade": Property.Finalidade.VENDA,
                "status": Property.Status.PUBLICADO,
                "destaque": True,
                "valor": Decimal("650000.00"),
                "valor_condominio": Decimal("580.00"),
                "valor_iptu": Decimal("1200.00"),
                "regiao": bessa,
                "cidade": "João Pessoa",
                "bairro": "Bessa",
                "endereco": "Rua exemplo, 100",
                "cep": "58000-000",
                "area_total": Decimal("95.00"),
                "area_privativa": Decimal("82.00"),
                "quartos": 3,
                "suites": 1,
                "banheiros": 2,
                "vagas": 2,
                "aceita_financiamento": True,
                "mobiliado": False,
                "possui_piscina": True,
                "possui_academia": True,
                "possui_elevador": True,
                "possui_area_gourmet": True,
                "titulo_seo": "Apartamento no Bessa em João Pessoa",
                "descricao_seo": "Apartamento à venda no Bessa com 3 quartos e lazer completo.",
            },
        )
        Property.objects.get_or_create(
            titulo="Casa em condomínio no Altiplano",
            defaults={
                "descricao": "Casa ampla para família, com área gourmet e piscina.",
                "tipo": Property.Tipo.CONDOMINIO,
                "finalidade": Property.Finalidade.VENDA,
                "status": Property.Status.PUBLICADO,
                "destaque": True,
                "valor": Decimal("1250000.00"),
                "valor_condominio": Decimal("900.00"),
                "valor_iptu": Decimal("2400.00"),
                "regiao": altiplano,
                "cidade": "João Pessoa",
                "bairro": "Altiplano",
                "endereco": "Condomínio exemplo",
                "cep": "58000-001",
                "area_total": Decimal("240.00"),
                "area_privativa": Decimal("180.00"),
                "quartos": 4,
                "suites": 3,
                "banheiros": 5,
                "vagas": 3,
                "aceita_financiamento": True,
                "mobiliado": True,
                "possui_piscina": True,
                "possui_academia": False,
                "possui_elevador": False,
                "possui_area_gourmet": True,
            },
        )
        Property.objects.get_or_create(
            titulo="Rascunho interno de terreno",
            defaults={
                "descricao": "Este imóvel não aparece na listagem pública.",
                "tipo": Property.Tipo.TERRENO,
                "finalidade": Property.Finalidade.VENDA,
                "status": Property.Status.RASCUNHO,
                "valor": Decimal("300000.00"),
                "cidade": "João Pessoa",
                "bairro": "Portal do Sol",
            },
        )

        Banner.objects.get_or_create(
            titulo="Encontre seu imóvel em João Pessoa",
            defaults={
                "subtitulo": "Curadoria de imóveis para venda e aluguel.",
                "imagem": "banners/banner-home.jpg",
                "botao_texto": "Ver imóveis",
                "botao_link": "/imoveis",
                "ativo": True,
                "ordem": 1,
            },
        )
        self.stdout.write(self.style.SUCCESS("Seed concluido."))
