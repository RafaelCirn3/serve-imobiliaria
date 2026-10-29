from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("banners", "0003_propertycarousel")]

    operations = [
        migrations.CreateModel(
            name="SectionImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("section", models.CharField(choices=[("tourism", "Pontos turísticos"), ("investment", "Orla e investimentos")], max_length=20)),
                ("image", models.ImageField(upload_to="home_sections/")),
                ("caption", models.CharField(blank=True, max_length=180)),
                ("active", models.BooleanField(default=True)),
                ("position", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ("position", "id")},
        )
    ]
