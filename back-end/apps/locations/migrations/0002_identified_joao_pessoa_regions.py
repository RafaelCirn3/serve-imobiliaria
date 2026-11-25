from django.db import migrations


def seed(apps, schema_editor):
    Region = apps.get_model("locations", "Region")
    for name in ("Altiplano", "Cabo Branco", "Jardim Oceania", "Tambaú", "Brisamar", "Bessa"):
        Region.objects.get_or_create(nome=name, cidade="João Pessoa", defaults={"ativo": True})


class Migration(migrations.Migration):
    dependencies = [("locations", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
