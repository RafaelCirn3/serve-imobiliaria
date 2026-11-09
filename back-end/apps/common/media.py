"""Serve uploaded pictures behind the existing /media/ reverse proxy, including production."""
from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404
from django.views.decorators.http import require_safe

IMAGE_TYPES = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
               '.webp': 'image/webp', '.gif': 'image/gif', '.avif': 'image/avif',
               '.heic': 'image/heic', '.heif': 'image/heif'}


@require_safe
def uploaded_picture(request, path):
    root = Path(settings.MEDIA_ROOT).resolve()
    picture = (root / path).resolve()
    if not picture.is_relative_to(root) or picture.suffix.lower() not in IMAGE_TYPES or not picture.is_file():
        raise Http404('Imagem não encontrada.')
    try:
        stream = picture.open('rb')
    except OSError:
        raise Http404('Imagem não encontrada.')
    response = FileResponse(stream, content_type=IMAGE_TYPES[picture.suffix.lower()])
    response['Cache-Control'] = 'public, max-age=3600'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
