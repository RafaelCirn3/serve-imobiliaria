from django.db import models


class SectionImage(models.Model):
    class Section(models.TextChoices):
        TOURISM = "tourism", "Pontos turísticos"
        INVESTMENT = "investment", "Orla e investimentos"

    section = models.CharField(max_length=20, choices=Section.choices)
    image = models.ImageField(upload_to="home_sections/")
    caption = models.CharField(max_length=180, blank=True)
    active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("position", "id")

    def __str__(self):
        return f"{self.get_section_display()} - {self.caption or self.pk}"
