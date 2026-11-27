from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("properties", "0007_rotating_parking_launch")]
    operations = [
        migrations.AlterField(
            model_name="property", name="tipo",
            field=models.CharField(max_length=20, choices=[
                ("apartamento", "Apartamento"), ("casa", "Casa"),
                ("cobertura", "Cobertura"), ("terreno", "Área/Terreno"),
                ("comercial", "Comercial"), ("condominio", "Condomínio fechado"),
                ("flat", "Flat"), ("lancamento", "Lançamento"),
                ("em_construcao", "Em construção"), ("novo", "Novo"),
                ("pronto", "Pronto"),
            ]),
        ),
    ]
