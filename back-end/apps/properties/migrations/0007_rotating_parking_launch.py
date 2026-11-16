from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("properties", "0006_location_precision")]
    operations = [
        migrations.AddField(
            model_name="property", name="vagas_rotativas",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="property", name="tipo",
            field=models.CharField(max_length=20, choices=[
                ("apartamento", "Apartamento"), ("casa", "Casa"),
                ("cobertura", "Cobertura"), ("terreno", "Área/Terreno"),
                ("comercial", "Comercial"), ("condominio", "Condomínio fechado"),
                ("flat", "Flat"), ("lancamento", "Lançamento"),
            ]),
        ),
    ]
