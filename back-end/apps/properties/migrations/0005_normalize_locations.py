import unicodedata
from django.db import migrations


def normalize_locations(apps, schema_editor):
    Property = apps.get_model("properties", "Property")
    for property in Property.objects.using(schema_editor.connection.alias).all().iterator():
        values = {}
        for field in ("cidade", "bairro", "logradouro"):
            value = " ".join(getattr(property, field).split())
            values[f"{field}_busca"] = "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c)).casefold()
        values["cep"] = property.cep.replace("-", "").strip()
        Property.objects.using(schema_editor.connection.alias).filter(pk=property.pk).update(**values)


class Migration(migrations.Migration):
    dependencies = [("properties", "0004_structured_address")]
    operations = [migrations.RunPython(normalize_locations, migrations.RunPython.noop)]
