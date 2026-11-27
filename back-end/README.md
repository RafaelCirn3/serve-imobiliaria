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

Também são aceitos `lancamento` (Lançamento), `em_construcao` (Em construção),
`novo` (Novo) e `pronto` (Pronto) no campo `tipo`.

## Robô de fontes do Google Drive

O MVP MGA extrai as tabelas com texto primeiro e OCR local como fallback, mantendo
evidências e candidatos antes de criar imóveis em rascunho. Há CLI, API com JWT
administrativo e servidor MCP stdio. Execução de demonstração no Windows:
`mga-demo.cmd` dentro de `back-end`. Guia: [MVP MGA](../docs/robot-mga-mvp.md).

As 16 fontes padrão incluem **EMPREENDIMENTOS**, **TABELAS MGA CONSTRUCOES** e as
14 pastas adicionais listadas em `apps/robot/sources.py`. As adicionais usam nomes
de **Fonte adicional 01** a **Fonte adicional 14**, editáveis no admin; o inventário
consulta os nomes reais das pastas no Drive. Execute `python manage.py migrate`
para cadastrar as novas fontes, preservando nomes e estados das já existentes.
Elas são cadastradas pela migração e podem ser ativadas, desativadas ou ampliadas no
Django admin em **Fontes do Drive**. Compartilhe todas as pastas com o e-mail da
conta de serviço do Google com permissão de leitura e ative a Google Drive API no
projeto dessa conta. Configure uma das opções no back-end:

```dotenv
GOOGLE_DRIVE_CREDENTIALS_JSON={"type":"service_account",...}
# ou, para execução local:
GOOGLE_DRIVE_CREDENTIALS_FILE=/caminho/privado/credenciais.json
```

O JSON deve estar em uma linha e fora do repositório. Se nenhuma opção for definida,
o robô tenta as credenciais padrão da aplicação (ADC). Em Docker, o caminho de um
arquivo precisa existir **dentro** do contêiner; a variável JSON evita esse volume.
Para pastas configuradas como **Qualquer pessoa com o link**, também é possível usar
`GOOGLE_DRIVE_API_KEY` em `back-end/.env`. A chave de API não acessa pastas restritas;
nesse caso, use a conta de serviço e compartilhe cada pasta com o e-mail dela.
Se houver chave de API e credenciais de conta de serviço, estas têm prioridade.
No PowerShell local, após ativar o ambiente virtual, também é possível definir o
arquivo apenas para a sessão atual:

```powershell
$env:GOOGLE_DRIVE_CREDENTIALS_FILE = 'C:\caminho\privado\credenciais.json'
python manage.py mapear-fontes
```

O Celery Beat agenda `consultar_fontes_drive` a cada 24 horas, com Redis como broker.
O worker percorre as subpastas e páginas da API do Drive. Para cada pasta de primeiro
nível que contenha arquivos, cria uma **divulgação encontrada** pendente de revisão
no Django admin. Arquivos na raiz viram uma divulgação da própria fonte. Novas
execuções atualizam a lista de arquivos sem duplicar a divulgação nem alterar uma
decisão de revisão. Esses registros **não são imóveis publicados**: preço, endereço,
tipo e conteúdo editorial devem ser conferidos antes do cadastro em `Imóveis`.

Para executar a consulta imediatamente, com o worker ativo:

```bash
celery -A config call apps.robot.tasks.consultar_fontes_drive
```

### Planilha de mapeamento manual

Execute dentro de `back-end`:

```bash
python manage.py mapear-fontes
python manage.py mapear-fontes --output reports/minhas-fontes.xlsx
python manage.py mapear-filtros --output reports/materiais-filtrados.xlsx
```

`mapear-fontes` inclui todas as pastas e arquivos das fontes ativas.
`mapear-filtros` inclui apenas materiais com categoria identificada pelos perfis
e sem exclusões. A V2 preserva a hierarquia completa para auditar os descartes,
e acrescenta abas de revisão, cobertura, duplicidades, regras e auditoria.
Ambos aceitam `--source ID_DA_PASTA`. Detalhes em `apps/robot/README.md`.

O comando é **manual** e não integra a rotina diária. A planilha `.xlsx` tem abas
Resumo, Fontes, Pastas e Arquivos, com caminhos completos, níveis, IDs, links,
tipos MIME, tamanhos e datas informados pelo Drive. Ela inclui pastas vazias e
consulta todas as páginas de cada pasta. O destino padrão é `reports/`, ignorado
pelo Git. Falhas de uma fonte são isoladas, e a execução parcial é explicitamente
identificada; `--strict` interrompe na primeira falha. Se todas falharem, não há XLSX.
O mapeamento apenas lê o Drive e não altera os registros de divulgação.
Se o PostgreSQL estiver indisponível, o comando usa as 16 fontes padrão e avisa
no terminal. Fontes adicionadas no Django admin exigem conexão com o banco para
aparecer na planilha. A rotina diária do robô sempre exige o banco de dados.

Também é possível reprocessar o inventário completo sem banco nem Drive:

```bash
python manage.py mapear-filtros --input-inventory reports/mapa-fontes-20261124-203554.xlsx --compare-to reports/mapa-filtros-20261124-210140.xlsx --output reports/mapa-filtros-v2.xlsx --comparison-output reports/comparativo-v1-v2.xlsx
```

O CSV de amostra gerado junto ao mapa permite homologação humana e cálculo
posterior com `avaliar-filtros`. Sem rótulos humanos, não há estimativa de acurácia.

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
