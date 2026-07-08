from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Region",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=120)),
                ("cidade", models.CharField(default="João Pessoa", max_length=120)),
                ("descricao", models.TextField(blank=True)),
                ("imagem", models.ImageField(blank=True, null=True, upload_to="regioes/")),
                ("ativo", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["cidade", "nome"],
                "unique_together": {("nome", "cidade")},
            },
        ),
    ]
