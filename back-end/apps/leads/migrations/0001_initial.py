from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("properties", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Lead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("telefone", models.CharField(max_length=30)),
                ("mensagem", models.TextField(blank=True)),
                ("origem", models.CharField(choices=[("formulario", "Formulario"), ("whatsapp", "WhatsApp"), ("botao_contato", "Botao de contato")], default="formulario", max_length=30)),
                ("status", models.CharField(choices=[("novo", "Novo"), ("em_atendimento", "Em atendimento"), ("finalizado", "Finalizado"), ("descartado", "Descartado")], default="novo", max_length=30)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("imovel", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="leads", to="properties.property")),
            ],
            options={
                "ordering": ["-criado_em"],
            },
        ),
    ]
