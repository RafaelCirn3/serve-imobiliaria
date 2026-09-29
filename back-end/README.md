# SERVE Negócios Imobiliários API

API REST em Django + Django REST Framework para cadastro administrativo e consulta pública de imóveis da SERVE.

## Stack

- Django 5
- Django REST Framework
- PostgreSQL
- JWT com `djangorestframework-simplejwt`
- Swagger/OpenAPI com `drf-spectacular`
- Docker Compose

## Como executar

```bash
cd back-end
cp .env.example .env
docker compose up --build
```

A API ficara em:

- API: `http://localhost:8000/api/`
- Swagger: `http://localhost:8000/api/docs/`
- Django admin: `http://localhost:8000/admin/`

O comando de inicialização executa `migrate` e `seed`.

Usuario inicial:

- login: `admin`
- senha: `admin123`

## Autenticação

```http
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/auth/logout/
```

Use o access token retornado no header:

```http
Authorization: Bearer <access_token>
```

## Endpoints públicos

```http
GET  /api/imoveis/
GET  /api/imoveis/{slug}/
GET  /api/imoveis/destaques/
GET  /api/imoveis/busca/?q=termo
POST /api/leads/
GET  /api/regioes/
GET  /api/banners/
```

Filtros aceitos em `/api/imoveis/`:

```text
cidade, bairro, tipo, finalidade, valor_min, valor_max,
quartos, suites, vagas, area_min, area_max, destaque, ordering
```

Observação: a API pública sempre restringe imóveis a `status=publicado`.

## Endpoints administrativos

Todos exigem JWT de usuario com `is_staff=True`.

```http
POST   /api/admin/imoveis/
PUT    /api/admin/imoveis/{id}/
PATCH  /api/admin/imoveis/{id}/
DELETE /api/admin/imoveis/{id}/

POST   /api/admin/imoveis/{id}/imagens/
PATCH  /api/admin/imoveis/{id}/imagens/{imagem_id}/
DELETE /api/admin/imoveis/{id}/imagens/{imagem_id}/

GET    /api/admin/leads/
PATCH  /api/admin/leads/{id}/

POST   /api/admin/regioes/
PATCH  /api/admin/regioes/{id}/
DELETE /api/admin/regioes/{id}/

POST   /api/admin/banners/
PATCH  /api/admin/banners/{id}/
DELETE /api/admin/banners/{id}/
```

## Upload de imagens

Envie `multipart/form-data` para:

```http
POST /api/admin/imoveis/{id}/imagens/
```

Campos:

- `imagens`: um ou mais arquivos
- `legenda`: opcional
- `ordem`: opcional
- `imagem_capa`: `true` para marcar a primeira imagem enviada como capa

A regra de negócio garante apenas uma imagem de capa por imóvel.

## Regras implementadas

- Apenas imóveis publicados aparecem nos endpoints públicos.
- Endpoints administrativos exigem usuario autenticado e `is_staff`.
- Slug do imóvel é gerado automaticamente a partir do título.
- Exclusão administrativa de imóvel é lógica: status vira `inativo`.
- Leads podem ser criados publicamente e listados/atualizados apenas por admin.
- Listagens possuem paginação, filtros combinados, busca textual e ordenação.

## Tipos e perfil de busca

Os tipos aceitos são `apartamento`, `terreno` (Área/Terreno), `casa`,
`condominio` (Condomínio fechado), `flat`, `cobertura` e `comercial`.
Os identificadores existentes foram preservados. Aplique a migração com
`python manage.py migrate` no ambiente configurado antes de utilizar a nova versão.

`area_min` e `area_max` continuam filtrando **área privativa** em m².
`area_total_min` e `area_total_max` filtram **área total**, inclusive terrenos
sem área privativa. As faixas são inclusivas e combinadas com cidade, bairro,
tipo, valor e quantidade mínima de quartos. Valores negativos e faixas com
mínimo maior que máximo retornam HTTP 400.

Exemplo: `/api/imoveis/?tipo=terreno&cidade=Bananeiras&area_total_min=300&area_total_max=500`.
O `count` dos endpoints públicos considera somente imóveis publicados.

## Testes isolados

Após instalar `requirements.txt`, execute:

```powershell
python manage.py check --settings=config.test_settings
python manage.py makemigrations --check --dry-run --settings=config.test_settings
python manage.py test apps.properties --settings=config.test_settings
```

Essa configuração utiliza SQLite em memória e não acessa o PostgreSQL da aplicação.
Ela verifica os contratos e filtros desta etapa; a validação das migrações no PostgreSQL
deve ocorrer no ambiente de implantação. Não utilize `config.test_settings` em produção.

## Ofertas de venda e Gmail SMTP

O botão flutuante e o CTA de proprietários abrem o mesmo modal. A submissão faz
`POST /api/leads/venda-imovel/` com contato, descrição, dados opcionais do imóvel
e `idempotency_key` UUID. Repetir a mesma chave e o mesmo conteúdo recupera o
protocolo anterior; conteúdo diferente com a mesma chave retorna 409.
O limite anônimo é de 5 chamadas/hora por IP, separado das consultas de endereço.

O lead é salvo antes de tentar o envio. A resposta contém apenas `id` e
`notificacao_status` (`enviado` ou `falhou`); a interface não anuncia envio de
e-mail quando ele falha. Repetir o POST não reenvia a mensagem. Ofertas ficam
disponíveis no painel de leads, com dados do imóvel e estado da notificação.

Configure no arquivo **não versionado** `back-end/.env`:

```dotenv
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=conta-remetente@gmail.com
EMAIL_HOST_PASSWORD=senha-de-aplicativo-sem-espacos
DEFAULT_FROM_EMAIL=conta-remetente@gmail.com
SALE_EMAIL_ENABLED=True
EMAIL_TIMEOUT=10
```

Use uma conta com verificação em duas etapas e uma
[senha de aplicativo do Google](https://support.google.com/mail/answer/185833?hl=pt-BR).
O remetente deve corresponder à conta autenticada. `Reply-To` aponta para o
proprietário e o destinatário é fixo: **Servenegociosimobiliarios@gmail.com**.
Sem credenciais, as ofertas continuam registradas, mas a notificação fica pendente.
Nunca coloque a senha no front-end ou no controle de versão.

Após corrigir a configuração, use o botão **Reenviar e-mail** no painel ou execute:

```powershell
python manage.py retry_sale_notifications --limit 20
```

O comando processa somente ofertas pendentes/com falha. Notificações já enviadas
não são reenviadas. O estado `enviado` significa aceite pelo servidor SMTP, não
confirmação de leitura ou garantia de entrega na caixa de entrada. Se o servidor
SMTP aceitar uma mensagem e a conexão cair antes da confirmação, uma tentativa
posterior ainda pode duplicá-la; o assunto contém o protocolo para identificação.
Validar uma entrega real exige a configuração da conta e conferência da caixa destinatária.

## ViaCEP, bairros e ruas

```text
GET  /api/localizacao/cep/?cep=58010000
GET  /api/localizacao/enderecos/?cidade=João%20Pessoa&logradouro=Rua%20da%20Praia
GET  /api/localizacao/bairros/?cidade=Cabedelo
GET  /api/localizacao/ruas/?cidade=Cabedelo&bairro=Intermares
GET  /api/localizacao/mapa-config/
POST /api/localizacao/geocodificar/      (somente administrador)
GET  /api/imoveis/mapa/?cidade=Cabedelo
```

O ViaCEP usa timeout de 6 segundos e cache de 24 horas. Falhas e CEP inexistente
permitem preenchimento manual no modal/cadastro. Número e complemento não são
substituídos pelas consultas. A pesquisa de ruas respeita os critérios mínimos do
[ViaCEP](https://viacep.com.br/). Nenhuma varredura de CEPs é executada.

Os bairros e ruas dos filtros vêm dos imóveis **publicados**, agrupados por cidade
e bairro, com comparação sem diferenças de espaços, maiúsculas ou acentos.
As opções não representam um catálogo de todos os bairros oficiais.
`logradouro` e `cep` combinam com os demais filtros da listagem.

As migrações adicionam UF, logradouro, número e complemento e preenchem as chaves
de busca dos registros antigos. O campo `endereco` anterior é preservado como
referência no cadastro: revise o texto e preencha o logradouro antes de esperar que
um imóvel antigo apareça na seleção de ruas. A migração não tenta separar números
ou classificar ruas automaticamente a partir de texto livre.

## Mapa e geocodificação

Leaflet 1.9 e MarkerCluster são carregados sob demanda. O endpoint de mapa usa os
mesmos filtros públicos, independentemente da página da lista. Ele informa total,
quantidade com coordenadas, quantidade sem coordenadas e truncamento, com limite
configurável de 2.000 marcadores. A lista permanece disponível quando não há
coordenadas ou quando mapa/tiles falham.

No cadastro, **Localizar endereço no mapa** consulta Nominatim por ação explícita do
administrador, com cache de 30 dias e intervalo conservador entre chamadas. O
resultado pode ser corrigido arrastando o marcador ou editando as coordenadas; ele
é armazenado ao salvar, sem chamadas de geocodificação em visitas públicas.

Localizações são aproximadas por padrão: coordenadas públicas arredondadas a três
casas decimais e número/complemento ocultos. O administrador pode marcar posição
conferida e publicar os dados exatos. A listagem e o mapa do detalhe seguem a mesma regra.

O padrão utiliza tiles OpenStreetMap e Nominatim sem chave de API. Esses serviços
comunitários não garantem disponibilidade; são adequados ao uso inicial de baixo
volume. `MAP_TILE_URL`, `MAP_TILE_ATTRIBUTION` e `GEOCODER_URL` permitem trocar os
provedores no servidor, sem editar o front-end. Os tiles preservam atribuição e cache
do navegador; não há pré-carregamento em massa. A geocodificação usa identificação
da SERVE e não oferece autocomplete Nominatim. Referências:
[política de tiles](https://operations.osmfoundation.org/policies/tiles/) e
[política de geocodificação](https://operations.osmfoundation.org/policies/nominatim/).

Para múltiplos processos de produção, use cache compartilhado para limites/cache:

```dotenv
CACHE_BACKEND=django.core.cache.backends.db.DatabaseCache
CACHE_LOCATION=serve_cache
```

Depois de configurar o PostgreSQL e aplicar `python manage.py migrate`, execute
`python manage.py createcachetable`. O padrão `LocMemCache` é destinado ao
desenvolvimento em um processo. Tiles e geocodificação em maior escala podem
exigir plano comercial; os custos dependem do provedor escolhido.

## Verificação das novas funcionalidades

```powershell
python manage.py test apps.leads apps.locations apps.properties --settings=config.test_settings
python manage.py check
python manage.py makemigrations --check --dry-run --settings=config.test_settings
```

Os testes cobrem captação, idempotência, falha/reenvio de e-mail, limitação de
chamadas, ViaCEP simulado, filtros dependentes, mapa além da primeira página e
exposição aproximada/exata de coordenadas. A verificação local utiliza e-mails
em memória, sem envio para destinatários externos.

O telefone da oferta deve conter entre 10 e 15 dígitos, permitindo DDD, código
internacional, espaços, parênteses e hífens. Os limites por IP de ofertas (5/hora)
e consultas de endereço (60/hora) também se aplicam a usuários autenticados.
