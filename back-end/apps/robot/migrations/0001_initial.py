from django.db import migrations, models
import django.db.models.deletion


def create_sources(apps, schema_editor):
    Source = apps.get_model("robot", "DriveSource")
    for name, folder_id in (
        ("EMPREENDIMENTOS", "1YLnoMqt0exRBUw5sGf6CbbSbGXqfPFxw"),
        ("TABELAS MGA CONSTRUCOES", "1STtG3FBmaLAeOPVLxQlZyL_OY7T9617n"),
    ):
        Source.objects.using(schema_editor.connection.alias).get_or_create(pasta_id=folder_id, defaults={"nome": name})


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="DriveSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=120)),
                ("pasta_id", models.CharField(max_length=128, unique=True)),
                ("ativa", models.BooleanField(default=True)),
                ("ultima_consulta_em", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["nome"], "verbose_name": "Fonte do Drive", "verbose_name_plural": "Fontes do Drive"},
        ),
        migrations.CreateModel(
            name="DrivePublication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("pasta_id", models.CharField(max_length=128)),
                ("titulo", models.CharField(max_length=180)),
                ("caminho", models.TextField()),
                ("url_pasta", models.URLField(max_length=500)),
                ("arquivos", models.JSONField(default=list)),
                ("status", models.CharField(choices=[("pendente", "Pendente de revisão"), ("revisada", "Revisada"), ("ignorada", "Ignorada")], default="pendente", max_length=12)),
                ("criada_em", models.DateTimeField(auto_now_add=True)),
                ("atualizada_em", models.DateTimeField(auto_now=True)),
                ("fonte", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="divulgacoes", to="robot.drivesource")),
            ],
            options={"ordering": ["-criada_em"], "verbose_name": "Divulgação encontrada", "verbose_name_plural": "Divulgações encontradas"},
        ),
        migrations.AddConstraint(model_name="drivepublication", constraint=models.UniqueConstraint(fields=("fonte", "pasta_id"), name="unique_drive_publication_folder")),
        migrations.RunPython(create_sources, migrations.RunPython.noop),
    ]
