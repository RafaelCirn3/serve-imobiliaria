from uuid import uuid4
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase
from .models import Lead


class SaleLeadTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.payload = {"idempotency_key": str(uuid4()), "nome": "Proprietário", "email": "owner@example.test",
                        "telefone": "83999998888", "mensagem": "Apartamento com varanda", "tipo": "flat",
                        "cidade": "Cabedelo", "bairro": "Intermares", "valor": "450000.00"}

    def post_offer(self, payload=None):
        return self.client.post("/api/leads/venda-imovel/", payload or self.payload, format="json")

    def test_offer_is_saved_and_sent_to_fixed_recipient(self):
        response = self.post_offer()
        self.assertEqual(response.status_code, 201)
        lead = Lead.objects.get(pk=response.data["id"])
        self.assertEqual(lead.origem, "venda_imovel")
        self.assertIsNone(lead.imovel_id)
        self.assertEqual(lead.dados_imovel["tipo"], "flat")
        self.assertEqual(response.data["notificacao_status"], "enviado")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["Servenegociosimobiliarios@gmail.com"])
        self.assertEqual(mail.outbox[0].reply_to, ["owner@example.test"])
        self.assertIn("Apartamento com varanda", mail.outbox[0].body)

    def test_repeated_request_does_not_duplicate_lead_or_email(self):
        first = self.post_offer()
        second = self.post_offer()
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["id"], second.data["id"])
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_key_cannot_be_reused_for_different_payload(self):
        self.post_offer()
        response = self.post_offer(self.payload | {"mensagem": "Outros dados"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Lead.objects.count(), 1)

    @patch("apps.leads.notifications.EmailMessage.send", side_effect=OSError("smtp unavailable"))
    def test_email_failure_preserves_offer(self, send):
        response = self.post_offer()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["notificacao_status"], "falhou")
        self.assertEqual(Lead.objects.count(), 1)
        repeat = self.post_offer()
        self.assertEqual(repeat.status_code, 200)
        self.assertEqual(send.call_count, 1)

    @override_settings(SALE_EMAIL_ENABLED=False)
    def test_disabled_email_is_not_reported_as_sent(self):
        response = self.post_offer()
        self.assertEqual(response.data["notificacao_status"], "falhou")
        self.assertEqual(Lead.objects.count(), 1)

    def test_admin_can_retry_failed_email_once(self):
        with override_settings(SALE_EMAIL_ENABLED=False):
            response = self.post_offer()
        pk = response.data["id"]
        admin = get_user_model().objects.create_user(username="sale-admin", is_staff=True)
        self.client.force_authenticate(user=admin)
        for _ in range(2):
            response = self.client.post(f"/api/admin/leads/{pk}/reenviar-notificacao/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["notificacao_status"], "enviado")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Lead.objects.get(pk=pk).notificacao_tentativas, 2)

    def test_invalid_contact_and_honeypot_do_not_create_leads(self):
        for fields in ({"nome": " "}, {"email": "invalid"}, {"telefone": "abc"}, {"website": "spam"}, {"valor": -1}):
            with self.subTest(fields=fields):
                self.assertEqual(self.post_offer(self.payload | fields).status_code, 400)
        self.assertEqual(Lead.objects.count(), 0)

    def test_public_endpoint_has_rate_limit(self):
        for _ in range(5):
            self.assertIn(self.post_offer().status_code, [200, 201])
        self.assertEqual(self.post_offer().status_code, 429)

    def test_authenticated_requests_cannot_bypass_public_rate_limit(self):
        user = get_user_model().objects.create_user(username="offer-user")
        self.client.force_authenticate(user=user)
        for _ in range(5):
            self.assertIn(self.post_offer().status_code, [200, 201])
        self.assertEqual(self.post_offer().status_code, 429)

    def test_phone_requires_digits_and_accepts_international_format(self):
        for phone in ("++++++++++", "(83) 123-456", "1234567890123456"):
            with self.subTest(phone=phone):
                self.assertEqual(self.post_offer(self.payload | {"telefone": phone}).status_code, 400)
        response = self.post_offer(self.payload | {"telefone": "+55 (83) 99999-8888"})
        self.assertEqual(response.status_code, 201)

    def test_public_cannot_retry_or_forge_sale_origin(self):
        response = self.client.post("/api/leads/", {**self.payload, "origem": "venda_imovel"}, format="json")
        self.assertEqual(response.status_code, 400)
        response = self.client.post("/api/admin/leads/1/reenviar-notificacao/")
        self.assertIn(response.status_code, [401, 403])


class OfferPhotoTests(APITestCase):
    def setUp(self):
        import tempfile
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.directory.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        cache.clear()
        self.payload = {'idempotency_key': str(uuid4()), 'nome': 'Proprietário', 'email': 'owner@example.test',
                        'telefone': '83999998888', 'mensagem': 'Casa para alugar', 'finalidade': 'aluguel'}

    @staticmethod
    def photo(name='foto.png', color='blue', format='PNG'):
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        output = BytesIO()
        Image.new('RGB', (16, 16), color).save(output, format=format)
        return SimpleUploadedFile(name, output.getvalue(), content_type='image/' + format.lower())

    def test_public_offer_persists_multiple_photos_and_purpose(self):
        response = self.client.post('/api/leads/venda-imovel/', self.payload | {'fotos': [self.photo(), self.photo('outra.png', 'red')]}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        lead = Lead.objects.get(pk=response.data['id'])
        self.assertEqual(lead.fotos.count(), 2)
        self.assertEqual(lead.dados_imovel['finalidade'], 'aluguel')
        self.assertTrue(all(photo.imagem.name.endswith('.jpg') for photo in lead.fotos.all()))
        self.assertIn('Finalidade: aluguel', mail.outbox[0].body)
        self.assertIn('https://servenegociosimobiliarios.com.br/media/ofertas/', mail.outbox[0].body)
        admin = get_user_model().objects.create_user(username='photos-admin', is_staff=True)
        self.client.force_authenticate(user=admin)
        response = self.client.get(f'/api/admin/leads/{lead.pk}/')
        self.assertEqual(len(response.data['fotos']), 2)

    def test_photo_retry_does_not_duplicate_attachments(self):
        for expected in [201, 200]:
            response = self.client.post('/api/leads/venda-imovel/', self.payload | {'fotos': [self.photo()]}, format='multipart')
            self.assertEqual(response.status_code, expected, response.data)
        self.assertEqual(Lead.objects.get().fotos.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_idempotency_key_cannot_replace_photo_bytes(self):
        self.client.post('/api/leads/venda-imovel/', self.payload | {'fotos': [self.photo()]}, format='multipart')
        response = self.client.post('/api/leads/venda-imovel/', self.payload | {'fotos': [self.photo(color='red')]}, format='multipart')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Lead.objects.get().fotos.count(), 1)

    def test_invalid_photo_rejects_whole_offer(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        response = self.client.post('/api/leads/venda-imovel/', self.payload | {'fotos': [self.photo(), SimpleUploadedFile('bad.png', b'bad', content_type='image/png')]}, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Lead.objects.count(), 0)

    def test_heic_photo_is_converted(self):
        response = self.client.post('/api/leads/venda-imovel/', self.payload | {'fotos': [self.photo('iphone.heic', format='HEIF')]}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        from PIL import Image
        with Lead.objects.get().fotos.get().imagem.open('rb') as stream:
            with Image.open(stream) as image:
                self.assertEqual(image.format, 'JPEG')

    def test_too_many_photos_rejected(self):
        response = self.client.post('/api/leads/venda-imovel/', self.payload | {'fotos': [self.photo(f'{i}.png') for i in range(21)]}, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Lead.objects.count(), 0)
