from django.db import migrations


def seed(apps, schema_editor):
    apps.get_model("locations", "Region").objects.get_or_create(nome="Centro", cidade="Bananeiras", defaults={"ativo": True})


class Migration(migrations.Migration):
    dependencies = [("locations", "0002_identified_joao_pessoa_regions")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
