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
