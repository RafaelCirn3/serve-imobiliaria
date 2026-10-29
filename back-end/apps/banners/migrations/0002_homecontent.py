from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("banners", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="HomeContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hero_title", models.CharField(default="O Melhor de João Pessoa para o seu novo capítulo.", max_length=180)),
                ("hero_subtitle", models.TextField(default="Encontre os melhores imóveis e investimentos, e realize-se!")),
                ("featured_label", models.CharField(default="Curadoria SERVE", max_length=100)),
                ("featured_title", models.CharField(default="Imóveis em destaque", max_length=180)),
                ("regions_label", models.CharField(default="Localização importa", max_length=100)),
                ("regions_title", models.CharField(default="Regiões mais procuradas", max_length=180)),
                ("investment_label", models.CharField(default="Investir em João Pessoa", max_length=100)),
                ("investment_title", models.CharField(default="Orla, qualidade de vida e valorização em uma capital em movimento.", max_length=240)),
                ("investment_body", models.TextField(default="João Pessoa combina bairros consolidados, novas frentes de desenvolvimento e uma relação rara entre praia, serviços e tranquilidade urbana.")),
                ("investment_extra", models.TextField(default="A SERVE organiza essa leitura para quem quer decidir com segurança: localização, liquidez, padrão do imóvel e momento de mercado.")),
                ("owner_label", models.CharField(default="Para proprietários", max_length=100)),
                ("owner_title", models.CharField(default="Anuncie com apresentação premium e gestão direta.", max_length=180)),
                ("owner_body", models.TextField(default="Seu imóvel merece imagens fortes, texto objetivo e uma jornada de contato sem atrito.")),
                ("owner_button", models.CharField(default="Falar com a SERVE", max_length=80)),
            ],
        )
    ]
