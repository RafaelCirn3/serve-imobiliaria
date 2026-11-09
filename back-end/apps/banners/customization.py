import hashlib
import json
from urllib.parse import urlparse, unquote
from django.conf import settings
from django.db import transaction
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from apps.common.permissions import IsAdminUserOnly
from apps.common.images import prepare_images
from apps.locations.models import Region
from apps.locations.serializers import RegionSerializer
from .models import Banner, HomeContent, PropertyCarousel, SectionImage, SiteCustomization, CustomizationAsset
from .serializers import BannerSerializer, HomeContentSerializer, AdminPropertyCarouselSerializer, PublicPropertyCarouselSerializer, SectionImageSerializer
from .customization_schema import FIELDS, HOME_FIELDS, SECTIONS, merged_config, field_schema

COLLECTIONS = {'banners':(Banner,BannerSerializer,'imagem'), 'section_images':(SectionImage,SectionImageSerializer,'image'), 'regions':(Region,RegionSerializer,'imagem'), 'carousels':(PropertyCarousel,AdminPropertyCarouselSerializer,None)}


def bundle():
    config,_=SiteCustomization.objects.get_or_create(pk=1)
    home,_=HomeContent.objects.get_or_create(pk=1)
    data={'config':merged_config(config.data),'home':dict(HomeContentSerializer(home).data)}
    for key,(model,serializer,_) in COLLECTIONS.items():data[key]=list(serializer(model.objects.all().order_by('id'),many=True).data)
    revision=hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()
    return {**data,'revision':revision}


def validate_config(data):
    if not isinstance(data,dict) or set(data) != set(FIELDS)|{'layout'}:raise serializers.ValidationError({'config':'Configuração incompleta ou desconhecida.'})
    for page,fields in FIELDS.items():
        if not isinstance(data[page],dict) or set(data[page]) != {f[0] for f in fields}:raise serializers.ValidationError({'config':f'Campos inválidos em {page}.'})
        for key,label,kind,_ in fields:
            value=data[page][key]
            if not isinstance(value,str) or len(value)>(5000 if kind=='textarea' else 500):raise serializers.ValidationError({'config':f'{label}: texto inválido ou muito longo.'})
            if kind=='email':serializers.EmailField().run_validation(value)
            if kind=='phone' and (not value.isascii() or not value.isdigit() or not 10<=len(value)<=15):raise serializers.ValidationError({'config':'Informe WhatsApp apenas com dígitos, país e DDD.'})
            if kind=='image' and value:
                if not (value.startswith('/media/') or value.startswith('/assets/') or value.startswith('https://')):raise serializers.ValidationError({'config':f'{label}: imagem não enviada.'})
        if page=='general' and not data[page]['brand_name'].strip():raise serializers.ValidationError({'config':'Informe o nome da marca.'})
    layout=data['layout']
    if not isinstance(layout,dict) or set(layout)!=set(SECTIONS):raise serializers.ValidationError({'layout':'Páginas inválidas.'})
    for page,sections in SECTIONS.items():
        rows=layout[page]
        if not isinstance(rows,list) or any(not isinstance(row,dict) or not isinstance(row.get('id'),str) for row in rows):raise serializers.ValidationError({'layout':'Blocos inválidos.'})
        if not isinstance(rows,list) or len(rows)!=len(sections) or {r.get('id') for r in rows if isinstance(r,dict)}!={k for k,_ in sections}:raise serializers.ValidationError({'layout':f'Blocos inválidos em {page}.'})
        for row in rows:
            if set(row)!={'id','visible','spacing','align','tone'} or type(row['visible']) is not bool or row['spacing'] not in ['original','compact','normal','wide'] or row['align'] not in ['original','left','center','right'] or row['tone'] not in ['original','dark','light']:raise serializers.ValidationError({'layout':'Aparência de bloco inválida.'})
    return data


def resolve_image(url, instance, field, optional=False):
    if not url:
        if optional:return ''
        raise serializers.ValidationError({'image':'Selecione uma imagem antes de salvar.'})
    if not isinstance(url,str):raise serializers.ValidationError({'image':'Imagem inválida.'})
    path=unquote(urlparse(url).path)
    if not path.startswith('/media/'):raise serializers.ValidationError({'image':'Use uma imagem enviada pelo editor.'})
    name=path[len('/media/'):]
    if '..' in name.split('/') or '\\' in name:raise serializers.ValidationError({'image':'Caminho inválido.'})
    current=getattr(instance,field,None) if instance else None
    if current and current.name==name:return name
    if CustomizationAsset.objects.filter(image=name).exists():return name
    raise serializers.ValidationError({'image':'Imagem desconhecida. Selecione o arquivo novamente.'})


def validate_collection(key, rows):
    model,serializer_class,image_field=COLLECTIONS[key]
    if not isinstance(rows,list) or len(rows)>100:raise serializers.ValidationError({key:'Use no máximo 100 itens por grupo.'})
    existing={item.pk:item for item in model.objects.all()}; seen=set(); operations=[]
    allowed=set(serializer_class().fields)-{'id'}
    for row in rows:
        if not isinstance(row,dict) or set(row)-allowed-{'id'}:raise serializers.ValidationError({key:'Item inválido.'})
        pk=row.get('id')
        if pk is not None and (type(pk) is not int or pk not in existing or pk in seen):raise serializers.ValidationError({key:'Item removido ou duplicado. Recarregue o editor.'})
        if pk is not None:seen.add(pk)
        instance=existing.get(pk); values={k:v for k,v in row.items() if k!='id'}
        image=None
        if image_field:image=resolve_image(values.pop(image_field,None),instance,image_field,optional=key=='regions')
        if key=='banners' and values.get('botao_link'):
            link=values['botao_link']
            if not isinstance(link,str) or not (link.startswith('https://') or (link.startswith('/') and not link.startswith('//'))):raise serializers.ValidationError({key:'O botão deve apontar para uma página do site ou HTTPS.'})
        serializer=serializer_class(instance,data=values)
        if image_field:serializer.fields[image_field].required=False
        serializer.is_valid(raise_exception=True)
        operations.append((serializer,{image_field:image} if image_field else {}))
    return operations, set(existing)-seen


class PublicSiteContent(APIView):
    permission_classes=[AllowAny]
    def get(self,request):
        result=bundle()
        result['banners']=[r for r in result['banners'] if r['ativo']]
        result['section_images']=[r for r in result['section_images'] if r['active']]
        result['regions']=[r for r in result['regions'] if r['ativo']]
        result['carousels']=list(PublicPropertyCarouselSerializer(PropertyCarousel.objects.filter(ativo=True).prefetch_related('imoveis'),many=True,context={'request':request}).data)
        response=Response(result);response['Cache-Control']='no-store';return response


class AdminCustomization(APIView):
    permission_classes=[IsAdminUserOnly]
    def get(self,request):
        return Response({**bundle(),'fields':field_schema(),'home_fields':[{'key':k,'label':l,'type':t,'max':HomeContent._meta.get_field(k).max_length or 5000} for k,l,t in HOME_FIELDS],'sections':{p:dict(ss) for p,ss in SECTIONS.items()}})
    def put(self,request):
        if not isinstance(request.data,dict) or set(request.data)!= {'revision','config','home',*COLLECTIONS}:raise serializers.ValidationError({'detail':'Envie o documento completo carregado pelo editor.'})
        with transaction.atomic():
            config,_=SiteCustomization.objects.get_or_create(pk=1)
            config=SiteCustomization.objects.select_for_update().get(pk=1)
            if request.data['revision']!=bundle()['revision']:return Response({'detail':'O conteúdo foi alterado em outra sessão. Recarregue antes de publicar.'},status=status.HTTP_409_CONFLICT)
            values=validate_config(request.data['config'])
            home=HomeContentSerializer(HomeContent.objects.get(pk=1),data=request.data['home']);home.is_valid(raise_exception=True)
            operations={key:validate_collection(key,request.data[key]) for key in COLLECTIONS}
            home.save()
            for key,(items,deleted) in operations.items():
                for serializer,extra in items:serializer.save(**extra)
                COLLECTIONS[key][0].objects.filter(pk__in=deleted).delete()
            config.data=values;config.save()
        return self.get(request)


class AdminCustomizationUpload(APIView):
    permission_classes=[IsAdminUserOnly]
    parser_classes=[MultiPartParser,FormParser]
    def post(self,request):
        files=request.FILES.getlist('image')
        if len(files)!=1:raise serializers.ValidationError({'image':'Envie uma imagem por vez.'})
        image=prepare_images(files)[0]
        asset=CustomizationAsset.objects.create(image=image)
        return Response({'url':asset.image.url},status=201)
