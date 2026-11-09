from django.db import models
class SiteCustomization(models.Model):
    data = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
class CustomizationAsset(models.Model):
    image = models.ImageField(upload_to='customizacao/')
    created_at = models.DateTimeField(auto_now_add=True)
