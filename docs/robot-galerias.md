# Galerias automáticas do robô

## Ordem e quantidade

1. Até **2 fachadas**, nas primeiras posições, com a primeira como capa.
2. Até **4 imagens de área de lazer**.
3. Até **3 imagens de ambientes internos**.

Com esses limites, o teto é nove imagens. Havendo acervo suficiente, o total
varia entre **6 e 9**, dentro da faixa de 6–10 solicitada. A escolha é sortida
por imóvel, com semente persistida: repetir a importação não troca a galeria.
Se houver menos de seis imagens, a seleção fica `incompleto`, com aviso de
acervo insuficiente. Não se repetem arquivos nem se usam outros imóveis para
completar quantidade. Categorias ausentes são sinalizadas. Todas as imagens
automáticas ficam com `vistoria_pendente=true`, sem vistoria semântica automática.

## Avulsos

Um avulso recebe apenas imagens do acervo do próprio imóvel avulso. A associação
usa fonte, empreendimento e unidade, sem comparação aproximada de nomes. Sufixos
explícitos de localização, como `(Bananeiras PB)`, podem ser retirados do nome
para compará-lo à pasta mapeada.

Quando há vários avulsos no mesmo prédio, a pasta genérica do prédio não basta:
é necessário identificar apartamento, sala, loja ou lote. Torres e quadras são
respeitadas. Lote 190 da quadra K não recebe imagens do lote 190 da quadra L.
Sem vínculo inequívoco, o cadastro aguarda conferência, sem buscar fotos genéricas
de outra unidade. Nos empreendimentos regulares, fachada/lazer comuns podem ser
compartilhados; interiores identificados como de outra unidade/tipologia são excluídos.

## Comandos

Dentro de `back-end`, com ambiente virtual ativado:

```powershell
python manage.py vincular-imagens --inventario reports/mapa-fontes-20261124-203554.xlsx
python manage.py vincular-imagens --aplicar --output reports/mga/galerias.json
python manage.py vincular-imagens --imovel 4 --aplicar
```

O primeiro comando indexa e apresenta prévia; somente `--aplicar` baixa e vincula.
Na raiz, para o Docker local:

```powershell
docker compose exec -T api python manage.py migrate --noinput
docker compose exec -T api python manage.py vincular-imagens --inventario reports/mapa-fontes-20261124-203554.xlsx --aplicar --output reports/mga/galerias-postgres-local.json
```

`robot-mga --inventario ... --aplicar` também prepara o catálogo. O serviço de
importação compartilhado por CLI, API e MCP associa imagens depois de confirmar
a transação do imóvel. Em uploads individuais, o catálogo deve ter sido preparado
com o inventário. Um catálogo vazio gera `aguardando_acervo`. Falhas de imagens
não desfazem o imóvel, e a operação pode ser repetida. Galerias manuais existentes
são preservadas.

## Persistência

`DriveImageAsset` guarda fonte, arquivo, pasta, projeto e classificação.
`PropertyImageSelection` guarda semente, plano, contagens, faltas e erros.
`PropertyImage` recebe categoria, proveniência Drive, hash do conteúdo, ordem,
capa e pendência de vistoria. IDs ou conteúdos idênticos não se repetem no imóvel.
Os arquivos ficam no storage da plataforma; o navegador usa URLs locais.

As imagens são convertidas para JPEG de até 2560 pixels. O robô aceita originais
de até 64 MB, com decodificação reduzida quando suportada. Para originais grandes,
uma rendição autorizada do próprio Drive pode ser baixada no servidor. O link
temporário não é persistido nem exposto. O upload manual mantém seu limite
anterior de 10 MB por lote de até 20 fotos.

A API de importação e de consulta de unidades expõe `gallery`. Os serializers
de imagens expõem categoria e pendência, respeitando `ordem`. A associação não
publica os imóveis.

## Resultado local

Foram indexadas **1.633 imagens categorizadas com identidade de projeto**.
Os imóveis Makai 4 (unidade 1) e 5 (unidade 101) receberam, cada um, **2 fachadas
e 4 imagens de lazer**, totalizando seis fotos. Há seis candidatos de lazer no
acervo; são escolhidos quatro por galeria. Não há interiores classificados para
Makai, e `SEM_INTERNOS` permanece sinalizado.

A fachada de 38 MB foi vinculada usando uma rendição do próprio arquivo com
2560 × 2133 pixels. As 12 URLs locais retornaram HTTP 200; cada imóvel tem uma
única capa e as duas primeiras posições são fachadas. Os imóveis seguem como
rascunhos. Migrações aplicadas: properties/0010 e robot/0007.

Os testes cobrem cotas, ordem, capa, seleção estável/sortida, avulsos por unidade,
torre e quadra/lote, duplicidade de conteúdo, galerias manuais, arquivos grandes,
cache de rendição e associação após o commit.

Resultado dos testes: 94 testes de robô + imóveis passaram. A suíte completa
executou 143 testes, com os mesmos dois erros Windows preexistentes fora do robô
(arquivo aberto na limpeza do teste de banners e falta de privilégio para symlink).

Referência: [`thumbnailLink` da API do Drive](https://developers.google.com/workspace/drive/api/reference/rest/v3/files).
Não há validação automática de adequação visual; permanece a conferência humana.
