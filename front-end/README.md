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

## Funcionalidades públicas

- O CTA fixo **Quer vender seu imóvel? Descreva aqui!** e o botão de proprietários
  abrem um diálogo com navegação por teclado, Escape e retorno do foco. Ele é
  ocultado nas rotas administrativas. O formulário preserva dados quando há erro.
  O CTA recalcula sua posição após rolagem, redimensionamento e carregamento de
  conteúdo; fica temporariamente oculto quando coincidir com controles e preserva
  a atribuição do mapa.
- O editor de endereço consulta o ViaCEP pela API da SERVE e permite completar
  manualmente os campos. A busca por rua usa ViaCEP; as opções dos filtros vêm
  dos imóveis publicados no catálogo.
  Editar o CEP ou a rua cancela a consulta anterior imediatamente; respostas
  atrasadas não sobrescrevem edições manuais nem um endereço selecionado.
- Cidade, bairro e rua são dependentes. Alterar a cidade limpa bairro/rua e alterar
  o bairro limpa a rua. Filtros e modo Lista/Mapa são mantidos na URL.
  A pesquisa por várias palavras usa os mesmos critérios na lista e no mapa.
- O mapa usa Leaflet e agrupamento de marcadores, com popup e acesso ao detalhe.
  Imóveis sem coordenadas continuam disponíveis na lista. A configuração dos
  tiles vem da API; não há chaves de geocodificação ou credenciais SMTP no cliente.
- No cadastro administrativo, a localização pode ser sugerida pelo geocodificador
  e ajustada no mapa antes de salvar. A exposição pública é aproximada por padrão.
  Uma sugestão recebida após editar o endereço ou as coordenadas é descartada.

Configuração de SMTP, cache e mapa: consulte [o README do back-end](../back-end/README.md).
Para validar a compilação, execute `npm run build`. As APIs devem estar acessíveis
na URL configurada em `src/environments/environment.ts`.
