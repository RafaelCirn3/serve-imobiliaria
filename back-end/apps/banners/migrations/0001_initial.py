from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Banner",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=140)),
                ("subtitulo", models.CharField(blank=True, max_length=255)),
                ("imagem", models.ImageField(upload_to="banners/")),
                ("botao_texto", models.CharField(blank=True, max_length=80)),
                ("botao_link", models.CharField(blank=True, max_length=255)),
                ("ativo", models.BooleanField(default=True)),
                ("ordem", models.PositiveIntegerField(default=0)),
            ],
            options={
                "ordering": ["ordem", "id"],
            },
        ),
    ]
