from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("banners", "0002_homecontent"), ("properties", "0006_location_precision")]
    operations = [
        migrations.CreateModel(
            name="PropertyCarousel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=160)),
                ("subtitulo", models.CharField(blank=True, max_length=250)),
                ("ativo", models.BooleanField(default=True)),
                ("ordem", models.PositiveIntegerField(default=0)),
                ("imoveis", models.ManyToManyField(blank=True, related_name="carrosseis", to="properties.property")),
            ],
            options={"ordering": ["ordem", "id"]},
        ),
    ]
