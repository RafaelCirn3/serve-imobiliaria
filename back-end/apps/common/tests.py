from io import BytesIO
from pathlib import Path
import tempfile
from django.test import SimpleTestCase, override_settings
from PIL import Image


class ProductionMediaTests(SimpleTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / 'media'
        self.root.mkdir()
        self.override = override_settings(MEDIA_ROOT=self.root, DEBUG=False, SECURE_SSL_REDIRECT=False)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.picture = self.root / 'imoveis' / 'foto.jpg'
        self.picture.parent.mkdir()
        Image.new('RGB', (24, 16), 'blue').save(self.picture)

    def test_serves_actual_image_bytes_with_debug_disabled(self):
        response = self.client.get('/media/imoveis/foto.jpg')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        with Image.open(BytesIO(b''.join(response.streaming_content))) as image:
            self.assertEqual(image.size, (24, 16))
        response.close()

    def test_head_and_missing_file(self):
        response = self.client.head('/media/imoveis/foto.jpg')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response['Content-Length']), self.picture.stat().st_size)
        response.close()
        self.assertEqual(self.client.get('/media/imoveis/ausente.jpg').status_code, 404)

    def test_disallows_non_images_directories_and_write_methods(self):
        (self.root / 'config.txt').write_text('private')
        self.assertEqual(self.client.get('/media/config.txt').status_code, 404)
        self.assertEqual(self.client.get('/media/imoveis/').status_code, 404)
        self.assertEqual(self.client.post('/media/imoveis/foto.jpg').status_code, 405)

    def test_cannot_escape_media_root_even_through_symlinks(self):
        outside = Path(self.directory.name) / 'outside.jpg'
        outside.write_bytes(self.picture.read_bytes())
        (self.root / 'linked.jpg').symlink_to(outside)
        self.assertEqual(self.client.get('/media/../outside.jpg').status_code, 404)
        self.assertEqual(self.client.get('/media/linked.jpg').status_code, 404)
