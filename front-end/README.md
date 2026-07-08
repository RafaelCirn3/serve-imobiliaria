# SERVE Frontend

Frontend Angular da plataforma SERVE Negócios Imobiliários.

## Stack

- Angular
- TypeScript
- SCSS
- Angular Router
- Reactive Forms
- HttpClient
- JWT para area administrativa

## Executar somente o frontend

```bash
cd front-end
npm install
npm start
```

Aplicação: `http://localhost:4200`

## URL da API

Desenvolvimento:

```ts
// src/environments/environment.ts
apiUrl: 'http://localhost:8000/api'
```

Producao:

```ts
// src/environments/environment.prod.ts
apiUrl: 'https://seudominio.com.br/api'
```

## Rotas

Publicas:

- `/`
- `/imoveis`
- `/imoveis/:slug`
- `/sobre`
- `/contato`

Admin:

- `/admin/login`
- `/admin/dashboard`
- `/admin/imoveis`
- `/admin/imoveis/novo`
- `/admin/imoveis/:id/editar`
- `/admin/leads`
- `/admin/banners`
- `/admin/regioes`

## Subir frontend + backend

Na raiz do projeto:

```bash
docker compose up --build
```

Servicos:

- Frontend: `http://localhost:4200`
- API: `http://localhost:8000/api`
- Swagger: `http://localhost:8000/api/docs/`

Admin inicial gerado pelo backend:

- usuario: `admin`
- senha: `admin123`
