from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Property",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=180)),
                ("slug", models.SlugField(blank=True, max_length=220, unique=True)),
                ("descricao", models.TextField()),
                ("tipo", models.CharField(choices=[("apartamento", "Apartamento"), ("casa", "Casa"), ("cobertura", "Cobertura"), ("terreno", "Terreno"), ("comercial", "Comercial"), ("condominio", "Condomínio")], max_length=20)),
                ("finalidade", models.CharField(choices=[("venda", "Venda"), ("aluguel", "Aluguel")], max_length=20)),
                ("status", models.CharField(choices=[("rascunho", "Rascunho"), ("publicado", "Publicado"), ("vendido", "Vendido"), ("alugado", "Alugado"), ("inativo", "Inativo")], default="rascunho", max_length=20)),
                ("destaque", models.BooleanField(default=False)),
                ("valor", models.DecimalField(decimal_places=2, max_digits=14)),
                ("valor_condominio", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("valor_iptu", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("cidade", models.CharField(max_length=120)),
                ("bairro", models.CharField(max_length=120)),
                ("endereco", models.CharField(blank=True, max_length=255)),
                ("cep", models.CharField(blank=True, max_length=12)),
                ("latitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("longitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("area_total", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("area_privativa", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("quartos", models.PositiveSmallIntegerField(default=0)),
                ("suites", models.PositiveSmallIntegerField(default=0)),
                ("banheiros", models.PositiveSmallIntegerField(default=0)),
                ("vagas", models.PositiveSmallIntegerField(default=0)),
                ("aceita_financiamento", models.BooleanField(default=False)),
                ("mobiliado", models.BooleanField(default=False)),
                ("possui_piscina", models.BooleanField(default=False)),
                ("possui_academia", models.BooleanField(default=False)),
                ("possui_elevador", models.BooleanField(default=False)),
                ("possui_area_gourmet", models.BooleanField(default=False)),
                ("descricao_seo", models.CharField(blank=True, max_length=255)),
                ("titulo_seo", models.CharField(blank=True, max_length=180)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("publicado_em", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["-publicado_em", "-criado_em"],
            },
        ),
        migrations.CreateModel(
            name="PropertyImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("imagem", models.ImageField(upload_to="imoveis/")),
                ("legenda", models.CharField(blank=True, max_length=180)),
                ("ordem", models.PositiveIntegerField(default=0)),
                ("imagem_capa", models.BooleanField(default=False)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("imovel", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="imagens", to="properties.property")),
            ],
            options={
                "ordering": ["ordem", "id"],
            },
        ),
        migrations.AddIndex(
            model_name="property",
            index=models.Index(fields=["status", "destaque"], name="properties__status_81673a_idx"),
        ),
        migrations.AddIndex(
            model_name="property",
            index=models.Index(fields=["cidade", "bairro"], name="properties__cidade_eacd12_idx"),
        ),
        migrations.AddIndex(
            model_name="property",
            index=models.Index(fields=["tipo", "finalidade"], name="properties__tipo_f432bf_idx"),
        ),
    ]
