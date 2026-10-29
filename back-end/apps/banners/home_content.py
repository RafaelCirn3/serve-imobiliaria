from django.db import models


class HomeContent(models.Model):
    """Single editable public-home configuration."""
    hero_title = models.CharField(max_length=180, default="O Melhor de João Pessoa para o seu novo capítulo.")
    hero_subtitle = models.TextField(default="Encontre os melhores imóveis e investimentos, e realize-se!")
    featured_label = models.CharField(max_length=100, default="Curadoria SERVE")
    featured_title = models.CharField(max_length=180, default="Imóveis em destaque")
    regions_label = models.CharField(max_length=100, default="Localização importa")
    regions_title = models.CharField(max_length=180, default="Regiões mais procuradas")
    investment_label = models.CharField(max_length=100, default="Investir em João Pessoa")
    investment_title = models.CharField(max_length=240, default="Orla, qualidade de vida e valorização em uma capital em movimento.")
    investment_body = models.TextField(default="João Pessoa combina bairros consolidados, novas frentes de desenvolvimento e uma relação rara entre praia, serviços e tranquilidade urbana.")
    investment_extra = models.TextField(default="A SERVE organiza essa leitura para quem quer decidir com segurança: localização, liquidez, padrão do imóvel e momento de mercado.")
    owner_label = models.CharField(max_length=100, default="Para proprietários")
    owner_title = models.CharField(max_length=180, default="Anuncie com apresentação premium e gestão direta.")
    owner_body = models.TextField(default="Seu imóvel merece imagens fortes, texto objetivo e uma jornada de contato sem atrito.")
    owner_button = models.CharField(max_length=80, default="Falar com a SERVE")

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Conteúdo da página inicial"
