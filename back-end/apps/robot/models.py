from django.db import models
import uuid


class DriveSource(models.Model):
    nome = models.CharField(max_length=120)
    pasta_id = models.CharField(max_length=128, unique=True)
    ativa = models.BooleanField(default=True)
    ultima_consulta_em = models.DateTimeField(null=True, blank=True)
    perfil = models.JSONField(default=dict, blank=True, help_text="Origem, empresas relacionadas, agrupamento e filtros por categoria.")

    class Meta:
        ordering = ["nome"]
        verbose_name = "Fonte do Drive"
        verbose_name_plural = "Fontes do Drive"

    def __str__(self):
        return self.nome


class DriveProject(models.Model):
    chave = models.CharField(max_length=300, unique=True)
    nome = models.CharField(max_length=180)
    construtoras = models.JSONField(default=list)
    confianca = models.CharField(max_length=24, default="revisao")

    def __str__(self):
        return self.nome


class DrivePublication(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente de revisão"
        REVISADA = "revisada", "Revisada"
        IGNORADA = "ignorada", "Ignorada"

    fonte = models.ForeignKey(DriveSource, on_delete=models.PROTECT, related_name="divulgacoes")
    empreendimento = models.ForeignKey(DriveProject, null=True, blank=True, on_delete=models.PROTECT, related_name="origens")
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


class TableImport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.CharField(max_length=64, unique=True)
    content_sha256 = models.CharField(max_length=64)
    filename = models.CharField(max_length=255)
    source_folder_id = models.CharField(max_length=128, blank=True)
    drive_file_id = models.CharField(max_length=128, blank=True)
    developer_profile = models.CharField(max_length=40, default="mga")
    parser_version = models.CharField(max_length=40)
    context = models.JSONField(default=dict)
    extraction = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class TableUnit(models.Model):
    document = models.ForeignKey(TableImport, related_name="units", on_delete=models.CASCADE)
    index = models.PositiveIntegerField()
    fields = models.JSONField(default=dict)
    evidence = models.JSONField(default=dict)
    warnings = models.JSONField(default=list)
    reviewed = models.BooleanField(default=False)
    imported_property = models.ForeignKey("properties.Property", null=True, blank=True, on_delete=models.PROTECT, related_name="table_origins")
    imported_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["document", "index"], name="unique_table_unit_index")]


class ImportedUnitIdentity(models.Model):
    """Unidade física estável entre versões da tabela; imóveis existentes não são sobrescritos."""
    key = models.CharField(max_length=64, unique=True)
    property = models.OneToOneField("properties.Property", on_delete=models.PROTECT, related_name="robot_identity")


class DriveImageAsset(models.Model):
    source_id = models.CharField(max_length=128)
    file_id = models.CharField(max_length=128)
    folder_id = models.CharField(max_length=128)
    name = models.CharField(max_length=500)
    path = models.TextField()
    mime_type = models.CharField(max_length=120)
    project_name = models.CharField(max_length=300)
    project_normalized = models.CharField(max_length=300, db_index=True)
    category = models.CharField(max_length=16)
    url = models.URLField(max_length=1000)
    metadata = models.JSONField(default=dict)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["source_id", "file_id"], name="unique_source_image_asset")]


class PropertyImageSelection(models.Model):
    property = models.OneToOneField("properties.Property", on_delete=models.CASCADE, related_name="robot_gallery")
    seed = models.PositiveBigIntegerField()
    plan = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)
