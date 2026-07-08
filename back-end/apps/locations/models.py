from django.db import models


class Region(models.Model):
    nome = models.CharField(max_length=120)
    cidade = models.CharField(max_length=120, default="João Pessoa")
    descricao = models.TextField(blank=True)
    imagem = models.ImageField(upload_to="regioes/", null=True, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["cidade", "nome"]
        unique_together = ("nome", "cidade")

    def __str__(self):
        return f"{self.nome} - {self.cidade}"
