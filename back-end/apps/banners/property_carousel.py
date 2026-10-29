from django.db import models
from apps.properties.models import Property


class PropertyCarousel(models.Model):
    titulo = models.CharField(max_length=160)
    subtitulo = models.CharField(max_length=250, blank=True)
    imoveis = models.ManyToManyField(Property, blank=True, related_name="carrosseis")
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordem", "id"]

    def __str__(self):
        return self.titulo
