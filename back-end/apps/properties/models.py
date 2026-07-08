from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Property(models.Model):
    class Tipo(models.TextChoices):
        APARTAMENTO = "apartamento", "Apartamento"
        CASA = "casa", "Casa"
        COBERTURA = "cobertura", "Cobertura"
        TERRENO = "terreno", "Terreno"
        COMERCIAL = "comercial", "Comercial"
        CONDOMINIO = "condominio", "Condomínio"

    class Finalidade(models.TextChoices):
        VENDA = "venda", "Venda"
        ALUGUEL = "aluguel", "Aluguel"

    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        PUBLICADO = "publicado", "Publicado"
        VENDIDO = "vendido", "Vendido"
        ALUGADO = "alugado", "Alugado"
        INATIVO = "inativo", "Inativo"

    titulo = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    descricao = models.TextField()
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    finalidade = models.CharField(max_length=20, choices=Finalidade.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RASCUNHO)
    destaque = models.BooleanField(default=False)
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    valor_condominio = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    valor_iptu = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cidade = models.CharField(max_length=120)
    bairro = models.CharField(max_length=120)
    endereco = models.CharField(max_length=255, blank=True)
    cep = models.CharField(max_length=12, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    area_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    area_privativa = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quartos = models.PositiveSmallIntegerField(default=0)
    suites = models.PositiveSmallIntegerField(default=0)
    banheiros = models.PositiveSmallIntegerField(default=0)
    vagas = models.PositiveSmallIntegerField(default=0)
    aceita_financiamento = models.BooleanField(default=False)
    mobiliado = models.BooleanField(default=False)
    possui_piscina = models.BooleanField(default=False)
    possui_academia = models.BooleanField(default=False)
    possui_elevador = models.BooleanField(default=False)
    possui_area_gourmet = models.BooleanField(default=False)
    descricao_seo = models.CharField(max_length=255, blank=True)
    titulo_seo = models.CharField(max_length=180, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    publicado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-publicado_em", "-criado_em"]
        indexes = [
            models.Index(fields=["status", "destaque"]),
            models.Index(fields=["cidade", "bairro"]),
            models.Index(fields=["tipo", "finalidade"]),
        ]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._build_unique_slug()
        if self.status == self.Status.PUBLICADO and self.publicado_em is None:
            self.publicado_em = timezone.now()
        super().save(*args, **kwargs)

    def _build_unique_slug(self):
        base_slug = slugify(self.titulo) or "imovel"
        slug = base_slug
        counter = 2
        while Property.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug


class PropertyImage(models.Model):
    imovel = models.ForeignKey(Property, related_name="imagens", on_delete=models.CASCADE)
    imagem = models.ImageField(upload_to="imoveis/")
    legenda = models.CharField(max_length=180, blank=True)
    ordem = models.PositiveIntegerField(default=0)
    imagem_capa = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordem", "id"]

    def __str__(self):
        return f"Imagem {self.id} - {self.imovel}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.imagem_capa:
            PropertyImage.objects.filter(imovel=self.imovel, imagem_capa=True).exclude(pk=self.pk).update(imagem_capa=False)
