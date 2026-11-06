"""Validate complete upload batches before writing files; normalize phone photos."""
from io import BytesIO
from uuid import uuid4
import warnings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener
from rest_framework import serializers

register_heif_opener()


def prepare_images(files):
    if len(files) > 20 or sum(file.size for file in files) > 10 * 1024 * 1024:
        raise serializers.ValidationError('Envie até 20 fotos, somando no máximo 10 MB.')
    prepared = []
    for file in files:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(file) as image:
                    image.load()
                    image = ImageOps.exif_transpose(image)
                    image.thumbnail((2560, 2560))
                    image = image.convert('RGB')
                    output = BytesIO()
                    image.save(output, format='JPEG', quality=88)
            prepared.append(ContentFile(output.getvalue(), name=f'{uuid4().hex}.jpg'))
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise serializers.ValidationError(f'Não foi possível ler a foto {file.name}. Use JPEG, PNG, WebP ou HEIC.')
        finally:
            file.seek(0)
    return prepared
