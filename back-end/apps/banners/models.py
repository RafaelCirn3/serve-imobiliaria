from django.db import models


class Banner(models.Model):
    titulo = models.CharField(max_length=140)
    subtitulo = models.CharField(max_length=255, blank=True)
    imagem = models.ImageField(upload_to="banners/")
    botao_texto = models.CharField(max_length=80, blank=True)
    botao_link = models.CharField(max_length=255, blank=True)
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordem", "id"]

    def __str__(self):
        return self.titulo
