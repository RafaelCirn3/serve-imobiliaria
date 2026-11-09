from copy import deepcopy
from io import BytesIO
import tempfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from PIL import Image
from .models import Banner, HomeContent, PropertyCarousel, SiteCustomization
from apps.properties.models import Property


class CustomizationTests(APITestCase):
    def setUp(self):
        self.admin=get_user_model().objects.create_user(username='custom-admin',is_staff=True)
        self.client.force_authenticate(user=self.admin)
        self.banner=Banner.objects.create(titulo='Slide existente',imagem='banners/existente.jpg')
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.override=override_settings(MEDIA_ROOT=self.directory.name);self.override.enable();self.addCleanup(self.override.disable)

    def document(self):
        response=self.client.get('/api/admin/customizacao/')
        self.assertEqual(response.status_code,200)
        return {key:value for key,value in response.data.items() if key not in ['fields','home_fields','sections']}

    def put(self,data):return self.client.put('/api/admin/customizacao/',data,format='json')

    def test_initial_document_preserves_existing_home_and_images(self):
        HomeContent.objects.create(hero_title='Título do cliente')
        data=self.document()
        self.assertEqual(data['home']['hero_title'],'Título do cliente')
        self.assertEqual(data['banners'][0]['titulo'],'Slide existente')
        self.assertEqual(data['config']['general']['phone'],'5583988168587')

    def test_get_and_draft_do_not_publish_then_save_publishes(self):
        data=self.document();data['config']['about']['title']='Sobre personalizado'
        self.assertNotEqual(self.client.get('/api/site-content/').data['config']['about']['title'],'Sobre personalizado')
        response=self.put(data);self.assertEqual(response.status_code,200,response.data)
        self.assertEqual(self.client.get('/api/site-content/').data['config']['about']['title'],'Sobre personalizado')

    def test_all_pages_general_and_home_content_save_together(self):
        data=self.document()
        for page in ['home','properties','about','contact','detail']:data['config'][page][next(iter(data['config'][page]))]='Texto atualizado'
        data['config']['general']['phone']='5583988001122';data['home']['owner_button']='Anuncie aqui'
        response=self.put(data);self.assertEqual(response.status_code,200,response.data)
        self.assertEqual(HomeContent.objects.get(pk=1).owner_button,'Anuncie aqui')
        self.assertEqual(response.data['config']['general']['phone'],'5583988001122')

    def test_stale_revision_cannot_overwrite_another_save(self):
        data=self.document();other=deepcopy(data)
        data['config']['about']['title']='Primeiro';self.assertEqual(self.put(data).status_code,200)
        other['config']['about']['title']='Antigo';self.assertEqual(self.put(other).status_code,409)
        self.assertEqual(self.client.get('/api/site-content/').data['config']['about']['title'],'Primeiro')

    def test_legacy_content_update_is_also_detected_as_conflict(self):
        data=self.document();self.banner.titulo='Editado fora';self.banner.save()
        self.assertEqual(self.put(data).status_code,409)

    def test_invalid_collection_rolls_back_text_and_configuration(self):
        data=self.document();data['home']['hero_title']='Não pode salvar';data['config']['about']['title']='Também não'
        data['banners'][0]['titulo']=''
        response=self.put(data);self.assertEqual(response.status_code,400)
        self.assertNotEqual(HomeContent.objects.get(pk=1).hero_title,'Não pode salvar')
        self.assertNotEqual(SiteCustomization.objects.get().data.get('about',{}).get('title'),'Também não')

    def test_section_visibility_order_and_layout_are_saved(self):
        data=self.document();sections=data['config']['layout']['home'];sections.reverse();sections[0].update(visible=False,spacing='wide',align='center',tone='light')
        response=self.put(data);self.assertEqual(response.status_code,200,response.data)
        self.assertEqual(response.data['config']['layout']['home'],sections)

    def test_rejects_arbitrary_section_code_and_duplicate_ids(self):
        for change in ['code','duplicate','id']:
            data=self.document()
            if change=='code':data['config']['layout']['home'][0]['tone']='url(javascript:alert(1))'
            elif change=='duplicate':data['config']['layout']['home'][0]['id']=data['config']['layout']['home'][1]['id']
            else:data['config']['home']['custom_html']='<script>alert(1)</script>'
            self.assertEqual(self.put(data).status_code,400)

    def test_image_upload_is_draft_until_saved(self):
        output=BytesIO();Image.new('RGB',(32,24),'blue').save(output,format='PNG')
        response=self.client.post('/api/admin/customizacao/imagens/',{'image':SimpleUploadedFile('foto.png',output.getvalue(),content_type='image/png')},format='multipart')
        self.assertEqual(response.status_code,201,response.data)
        data=self.document();self.assertNotEqual(data['config']['general']['logo'],response.data['url'])
        data['banners'].append({'id':None,'titulo':'Novo slide','subtitulo':'','imagem':response.data['url'],'botao_texto':'','botao_link':'','ativo':True,'ordem':1})
        data['config']['general']['logo']=response.data['url']
        saved=self.put(data);self.assertEqual(saved.status_code,200,saved.data)
        self.assertEqual(Banner.objects.count(),2)
        self.assertEqual(self.client.get(response.data['url']).status_code,200)

    def test_collection_removal_only_happens_on_explicit_save(self):
        data=self.document();data['banners']=[];self.assertTrue(Banner.objects.exists())
        self.assertEqual(self.put(data).status_code,200);self.assertFalse(Banner.objects.exists())

    def test_public_bundle_does_not_expose_inactive_or_draft_properties(self):
        Banner.objects.create(titulo='Oculto',imagem='banners/oculto.jpg',ativo=False)
        property=Property.objects.create(titulo='Rascunho',descricao='Privado',tipo='casa',finalidade='venda',status='rascunho',cidade='João Pessoa',bairro='Centro',valor=1)
        carousel=PropertyCarousel.objects.create(titulo='Vitrine');carousel.imoveis.add(property)
        data=self.client.get('/api/site-content/').data
        self.assertEqual(len(data['banners']),1)
        self.assertEqual(data['carousels'][0]['properties'],[])

    def test_customization_and_upload_are_staff_only(self):
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get('/api/admin/customizacao/').status_code,[401,403])
        self.assertIn(self.client.post('/api/admin/customizacao/imagens/').status_code,[401,403])
        self.client.force_authenticate(user=get_user_model().objects.create_user(username='normal-user'))
        self.assertEqual(self.client.get('/api/admin/customizacao/').status_code,403)

    def test_invalid_links_and_unregistered_image_paths_are_rejected(self):
        for values in [{'botao_link':'javascript:alert(1)'},{'imagem':'/media/../../secret.jpg'},{'imagem':'/media/customizacao/unknown.jpg'}]:
            data=self.document();data['banners'][0].update(values);self.assertEqual(self.put(data).status_code,400)
