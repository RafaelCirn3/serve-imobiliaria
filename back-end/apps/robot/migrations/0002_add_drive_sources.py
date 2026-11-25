from django.db import migrations


def create_sources(apps, schema_editor):
    Source = apps.get_model("robot", "DriveSource")
    for name, folder_id in (
        ('Fonte adicional 01', '1KoTUVr7b-yabj3FmsxltctBYI-nqyz_j'),
        ('Fonte adicional 02', '1oy3n_5YPCaJkbMtQR6-x6t4EYlA6wH8Z'),
        ('Fonte adicional 03', '1ijReo1H-NoRDUWVj4y5ishlKhP4Fnr6P'),
        ('Fonte adicional 04', '1oyftGZQJ2PljwIyhiipsc2kuFsyW02rg'),
        ('Fonte adicional 05', '1xwjaaLOZVu3fstFeS2XNAYOwNtIRFMjr'),
        ('Fonte adicional 06', '1fuO2fVb8Wfs9UiL-8a6dIqLvBKTxTw_6'),
        ('Fonte adicional 07', '1fmX0Mizg-nqieM7yJeYKwtZpRSl8Mt11'),
        ('Fonte adicional 08', '1vhslZLYdG5AVq_WUcSfp4E0-k5zKyAQz'),
        ('Fonte adicional 09', '1bjgW5vrVyWG4hARHFIuoq3cj1w8191l3'),
        ('Fonte adicional 10', '1A7ExtgonjiVRYLX2j5eRNynUMG3aMqAA'),
        ('Fonte adicional 11', '1uL6-t71nzMdFxHrUgOmWo1nopsTI6NOj'),
        ('Fonte adicional 12', '1pd3kQuesg9gyaEfzQ4i53-jxc03nydLE'),
        ('Fonte adicional 13', '1usakkzKESKEx1k-JWZ_WwjwvWEqwGD1l'),
        ('Fonte adicional 14', '10AfFqutycPQYoxNoVM7o7q0UA5zEefdu'),
    ):
        Source.objects.using(schema_editor.connection.alias).get_or_create(
            pasta_id=folder_id, defaults={"nome": name}
        )


class Migration(migrations.Migration):
    dependencies = [("robot", "0001_initial")]
    operations = [migrations.RunPython(create_sources, migrations.RunPython.noop)]
