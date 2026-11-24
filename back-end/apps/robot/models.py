from django.db import models


class DriveSource(models.Model):
    nome = models.CharField(max_length=120)
    pasta_id = models.CharField(max_length=128, unique=True)
    ativa = models.BooleanField(default=True)
    ultima_consulta_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Fonte do Drive"
        verbose_name_plural = "Fontes do Drive"

    def __str__(self):
        return self.nome


class DrivePublication(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente de revisão"
        REVISADA = "revisada", "Revisada"
        IGNORADA = "ignorada", "Ignorada"

    fonte = models.ForeignKey(DriveSource, on_delete=models.PROTECT, related_name="divulgacoes")
    pasta_id = models.CharField(max_length=128)
    titulo = models.CharField(max_length=180)
    caminho = models.TextField()
    url_pasta = models.URLField(max_length=500)
    arquivos = models.JSONField(default=list)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDENTE)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criada_em"]
        constraints = [models.UniqueConstraint(fields=["fonte", "pasta_id"], name="unique_drive_publication_folder")]
        verbose_name = "Divulgação encontrada"
        verbose_name_plural = "Divulgações encontradas"

    def __str__(self):
        return self.titulo
