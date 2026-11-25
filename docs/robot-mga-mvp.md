# MVP MGA — extração e importação de tabelas

O MVP agora também vincula imagens conforme a [regra de galerias](robot-galerias.md):
fachadas primeiro, até quatro imagens de lazer e até três de internos. Avulsos
usam somente o acervo do próprio imóvel.

## Resultado entregue

O MVP processa tabelas da MGA com um parser orientado a objetos, compartilhado
por CLI, API administrativa e ferramentas MCP. Primeiro procura caracteres e
grades no PDF. Se a camada textual estiver vazia, danificada ou insuficiente,
renderiza somente a página necessária e executa OCR local com RapidOCR/ONNX.
PDFs nativos não precisam ser transformados integralmente em imagens.

Foram consultadas as nove tabelas comerciais selecionadas da fonte MGA, com
download limitado a esses documentos. A leitura página a página encontrou 24
páginas: 13 comerciais com texto/grades e 11 capas/apresentações que passaram
pelo fallback OCR. As unidades das tabelas nativas são extraídas diretamente.
Também foi executado OCR real sobre uma imagem da tabela de avulsos: as duas
linhas e os dois preços foram reconhecidos e sinalizados para conferência.

| Documento | Linhas mapeadas |
|---|---:|
| Avulsos MGA | 2 |
| Elevare | 170 |
| Essenza Park | 20 |
| Lumini | 27 |
| Makai | 2 |
| Mondo, incluindo lojas para locação | 20 |
| Sens | 6 |
| Soho | 7 |
| Soleil | 16 |
| **Total** | **270** |

Essas são linhas candidatas, não 270 anúncios prontos ou unidades disponíveis
homologadas. Há 48 linhas sem preço no Elevare; ausência de preço não é tratada
como prova de venda. Mondo inclui três lojas com locação mensal, separadas das
tabelas de venda e das parcelas de financiamento.

No banco SQLite isolado de demonstração, o processamento das nove tabelas criou
**dois rascunhos Makai**, com dados obrigatórios disponíveis no documento; as
outras **268 linhas** permaneceram para conferência. A repetição criou zero
imóveis e identificou os mesmos dois existentes. O teste MCP/API criou também
um rascunho da cobertura 2302 da tabela de avulsos, com finalidade de venda
declarada explicitamente no contexto de demonstração. Nenhum imóvel foi publicado
ou alterado no PostgreSQL configurado.

## Executar a demonstração no Windows

Na raiz do repositório:

```powershell
.\back-end\mga-demo.cmd
```

O lançador usa `.venv\Scripts\python.exe` quando disponível, aplica migrações em
`back-end/reports/mga-demo.sqlite3` e processa o PDF real de avulsos incluído nas
fixtures. Em uma base nova cria um rascunho da unidade 2302 e mantém o lote
pendente de bairro. Repetir o comando não duplica o imóvel. O resultado fica em
`back-end/reports/mga/demo-result.json`.

O arquivo de contexto da demonstração declara `finalidade=venda`; essa finalidade
não foi inferida apenas da palavra avulsos. O bairro ausente do lote não é
inventado. As dependências precisam estar instaladas no ambiente Python:

```powershell
.\.venv\Scripts\python.exe -m pip install -r back-end/requirements.txt
```

Para acessar os candidatos pelo Django admin da base de demonstração, execute
em `back-end` e crie suas próprias credenciais:

```powershell
python manage.py createsuperuser --settings=config.robot_demo_settings
python manage.py runserver --settings=config.robot_demo_settings
```

Os lançadores `.cmd` são executáveis de terminal que usam Python; não são binários
`.exe` autossuficientes. O Dockerfile também inclui as bibliotecas necessárias ao
OCR. O build da imagem Docker não foi executado nesta etapa.

## Processar as nove tabelas MGA

Dentro de `back-end`, com o ambiente virtual ativado:

```powershell
# Apenas mapear; não exige banco e não cria imóveis.
python manage.py robot-mga --inventario reports/mapa-fontes-20261124-203554.xlsx --baixar --output reports/mga/preview.json

# Salvar candidatos no banco configurado para conferência.
python manage.py robot-mga --inventario reports/mapa-fontes-20261124-203554.xlsx --salvar --output reports/mga/staged.json

# Importar somente linhas válidas como rascunhos, na base isolada de demonstração.
python manage.py migrate --settings=config.robot_demo_settings --noinput
python manage.py robot-mga --inventario reports/mapa-fontes-20261124-203554.xlsx --aplicar --output reports/mga/mvp-result.json --settings=config.robot_demo_settings
```

`--baixar` consulta somente as tabelas MGA selecionadas e atualiza seus arquivos
locais, com limite de 15 MB por documento. Sem essa opção, os PDFs precisam
existir em `reports/mga/input/<drive_file_id>.pdf`, permitindo replay offline.
O OCR/texto é reutilizado por SHA256 do conteúdo e versão do extrator. Uma versão
atualizada no Drive produz outro hash; imóveis existentes não são sobrescritos.

Para arquivo individual:

```powershell
python manage.py robot-mga --arquivo minha-tabela.pdf --empreendimento Makai --contexto contexto.json --salvar
```

O contexto é um objeto JSON simples ou contém `default` e `projects`. Exemplo
com informação expressamente fornecida pelo operador:

```json
{
  "projects": {
    "Makai": {"finalidade": "venda"}
  }
}
```

Campos aceitos no contexto: empreendimento, cidade, bairro, tipo, finalidade,
construtora e endereço. Cidade/bairro ausentes exigem dados verificados ou
revisão da unidade. Não use um bairro global para um catálogo de imóveis de
cidades diferentes. Uma finalidade global conflitante com a tabela de locação
é sinalizada e bloqueia a importação sem revisão explícita.

`--sem-ocr` desabilita o fallback; imagens puras falham explicitamente, enquanto
PDFs permanecem limitados à camada textual. `--cache-dir` e `--input-dir`
permitem outros diretórios. Os comandos mostram tempos e marcos. `--salvar`
persiste candidatos; `--aplicar` tenta criar rascunhos válidos e registra cada
pendência no JSON, sem abortar as demais linhas por erro de validação.

## Campos e regras de importação

O exemplo de avulsos foi mapeado para:

| Campo original | Destino |
|---|---|
| Empreendimento | `Property.empreendimento` |
| Unidade | `Property.unidade` |
| Torre/bloco, quando presente | `Property.torre` |
| Medidas | `Property.medidas` |
| Área (m²) sem natureza explícita | `Property.area_informada` |
| Valor total | `Property.valor`, com Decimal e duas casas |
| Endereço | `Property.endereco`; cidade/bairro apenas quando identificáveis |
| Descrição | `Property.descricao` |
| Empresa que fornece o catálogo | `Property.origem_comercial` |
| Responsável pelo empreendimento, quando identificado | `Property.construtora` |

Não se assume que a área genérica seja privativa ou total. Os campos existentes
`area_privativa` e `area_total` permanecem sem preenchimento automático nesses
casos. Dados ausentes continuam desconhecidos na extração; os defaults legados
do cadastro de imóveis não são tratados como evidência extraída.

Os números da imagem foram extraídos como `2820000.00`, área `300.00`, unidade
`2302`; e `370000.00`, área `400.00`, medidas `16x25m`, quadra K/lote 190. A
cobertura contém referência explícita a quatro vagas e mobiliário. O bairro
Brisamar e a cidade João Pessoa aparecem no endereço. O lote contém Bananeiras,
mas não há atribuição automática de bairro.

Na importação pelo inventário, identidades empresariais já mapeadas nos perfis
são usadas como contexto dos empreendimentos conhecidos; Elevare preserva
MGA/Tropical. Nos avulsos, MGA é origem comercial e o responsável continua
desconhecido. A finalidade locação é reconhecida pelo cabeçalho específico,
sem confundir mensalidade de financiamento com preço de aluguel.

`TableImport` mantém SHA256, versão, contexto, origem, texto por página e métodos.
`TableUnit` guarda campos normalizados, linha/página, células originais, condições
de pagamento preservadas, confiança, alertas, histórico de revisões e imóvel
associado. Arquivos enviados pela API não são publicados no diretório de mídia;
a API persiste os dados/evidências, não uma cópia do binário original.

Pré-requisitos para importar: empreendimento/unidade e campos obrigatórios do
cadastro válidos, preço positivo, cidade suportada, tipo, finalidade e bairro.
OCR, baixa confiança, tipologia/finalidade conflitantes e unidades repetidas
exigem aprovação explícita. A validação reutiliza `AdminPropertySerializer`.

A identidade da unidade inclui empreendimento normalizado, cidade, tipo,
finalidade, torre e unidade. Repetições reutilizam o vínculo existente. Em outra
versão de tabela, os valores anteriores não são sobrescritos; o valor da nova
tabela continua no candidato para revisão. Isso evita rebaixar um preço atualizado
com uma tabela histórica. Rascunhos nunca aparecem na API pública de imóveis.

## API administrativa

Todos os endpoints exigem JWT de usuário `is_staff=True`, usando o mesmo login
da plataforma. Eles também aparecem no schema da API. Não há endpoint público
de escrita do robô.

| Método | Endpoint | Uso |
|---|---|---|
| POST | `/api/admin/robot/mga/extracoes/` | Upload multipart de PDF/PNG/JPEG |
| GET | `/api/admin/robot/mga/extracoes/` | Listar extrações |
| GET | `/api/admin/robot/mga/extracoes/<uuid>/` | Unidades, evidências e pendências |
| GET | `/api/admin/robot/mga/unidades/<id>/` | Consultar candidato |
| PATCH | `/api/admin/robot/mga/unidades/<id>/` | Corrigir campos/aprovar |
| POST | `/api/admin/robot/mga/unidades/<id>/importar/` | Criar rascunho idempotente |

No upload: `arquivo`, `contexto` como JSON textual, `preview=true` para não
persistir, `ocr=false` para desabilitar OCR, e opcionalmente `source_folder_id`
e `drive_file_id`. Sem `preview`, salva os candidatos sem criar imóveis.

Revisão:

```json
{
  "fields": {"cidade": "João Pessoa", "bairro": "Brisamar", "finalidade": "venda"},
  "approve": true
}
```

A operação de importação retorna `imovel_id`, `criado`, `status` e
`dados_existentes_alterados=false`. Um imóvel novo sempre recebe `rascunho`.
`status=publicado` não é aceito na revisão da unidade. Imóveis já existentes só
podem ser alterados pelo fluxo administrativo normal da plataforma.

O Django admin também disponibiliza documentos e unidades para conferência, com
ação de importar rascunhos. Evidências/identificadores ficam somente para leitura
e essas áreas não permitem excluir o histórico pelo admin. A interface Angular
não ganhou uma tela própria de OCR nesta etapa; os novos campos estão disponíveis
nos serializers de imóveis e na área administrativa de conferência.

## MCP

O servidor implementado usa o SDK oficial MCP v1 fixado em dependência, transporte
**stdio**, e consome a mesma API com JWT. É um cliente local da API, não um endpoint
público `/mcp` sem autenticação. Para uma API remota, exige HTTPS; HTTP é permitido
para loopback de desenvolvimento.

Ferramentas:

- `mga_extrair_tabela`: base64, nome e contexto; por padrão apenas prévia.
- `mga_consultar_extracao`: dados/evidências por UUID.
- `mga_revisar_unidade`: alterações e aprovação explícita.
- `mga_importar_rascunho`: criação validada e idempotente.

No PowerShell, para uma API já em execução:

```powershell
$env:SERVE_API_URL = 'http://127.0.0.1:8000'
$env:SERVE_API_TOKEN = '<JWT de administrador>'
.\robot-mga-mcp.cmd
```

Exemplo de configuração de um cliente MCP, adaptando o caminho e o token:

```json
{
  "mcpServers": {
    "serve-mga": {
      "command": "C:\\Users\\Rafael\\Downloads\\serve\\.venv\\Scripts\\python.exe",
      "args": ["-m", "apps.robot.mcp_server"],
      "env": {
        "PYTHONPATH": "C:\\Users\\Rafael\\Downloads\\serve\\back-end",
        "SERVE_API_URL": "http://127.0.0.1:8000",
        "SERVE_API_TOKEN": "<JWT de administrador>"
      }
    }
  }
}
```

Tokens não são incluídos no código, fixtures ou relatórios. A renovação segue o
fluxo JWT existente da Serve. O transporte MCP HTTP remoto e OAuth dinâmico não
foram implementados; a integração entregue é stdio com API HTTP autenticada.
Clientes MCP devem aceitar o JSON textual retornado nas mensagens de conteúdo;
`structuredContent` é opcional no resultado do SDK utilizado.

## Verificação executada

História testada: documento MGA → extração → candidato → conferência → API
administrativa → transação no banco → rascunho → exclusão da consulta pública.

| Fronteira | Evidência |
|---|---|
| Fonte → documento | Nove PDFs comerciais reais baixados, sem varrer downloads de imagens |
| PDF → campos | Texto/grades nativos e fixture OCR real; valores da imagem conferidos |
| MCP → API | Handshake stdio e quatro ferramentas invocadas com SDK cliente real |
| API → banco | POST de extração, PATCH de revisão e importação na base SQLite demo |
| Banco → resposta | Rascunho retornado; repetição retorna o mesmo `imovel_id` |
| Isolamento público | `/api/imoveis/` permanece com zero resultados na demonstração |
| Autorização | Acesso anônimo à área do robô recebe 401; usuário comum recebe 403 em teste |

Artefatos locais, ignorados pelo Git em `reports/mga/`:

- `preview.json`: mapeamento das nove tabelas.
- `mvp-result.json`: primeira aplicação das nove tabelas, com dois rascunhos criados.
- `mvp-repeat-result.json`: zero criações e dois vínculos existentes.
- `ocr-avulsos.json`: duas linhas reconhecidas da versão em imagem.
- `smoke-mcp-api.json`: evidência do fluxo MCP/API/banco, sem credenciais.
- `demo-result.json`: resultado do lançador de demonstração.

Os testes adicionados cobrem formatos monetários, total versus parcelas, grades
reais das nove tabelas, torres repetindo números de unidade, locação, campo ausente,
OCR por coordenadas, aprovação, autorização, versão posterior, idempotência, CLI,
API e registro das ferramentas MCP. Foram executados **13 testes novos passando**
e **83 testes de robô + imóveis passando**. A suíte completa executou **132 testes**:
130 passaram e dois terminaram nos erros Windows já observados fora deste módulo
(limpeza de imagem aberta em banners e criação de symlink em common).

`check`, `makemigrations --check --dry-run` e `pip check` também foram executados.
Os três contratos novos (upload multipart, revisão e resultado da importação)
foram conferidos no OpenAPI gerado. O schema global ainda aponta erros de
introspecção em controllers preexistentes de banners/localização e avisos em
serializers antigos; esses componentes não foram alterados nesta tarefa.
As migrações são aditivas: properties/0009 e robot/0006. Foram aplicadas somente
na base de demonstração; para o banco do ambiente de execução use o fluxo normal
`python manage.py migrate` antes de usar os endpoints.

## Limitações do MVP

- O mapeamento cobre os padrões MGA observados, não documentos de qualquer construtora.
- Não há precisão/recall estatísticos homologados de todos os campos das 270 linhas.
- OCR não autoriza importar preço automaticamente; exige conferência explícita.
- As 268 linhas pendentes exigem complementar contexto ou resolver alertas; não são descartadas.
- Endereços e disponibilidade não são completados por suposição.
- Preços de imóveis existentes não são atualizados automaticamente.
- A identidade de importação impede repetir as mesmas unidades importadas; não faz fusão aproximada com imóveis manuais que não possuam vínculo de importação.
- A extração HTTP é síncrona. Digitalizações grandes devem usar CLI/worker e timeout compatível; o fluxo não foi transformado em fila de OCR nesta versão.
- Limites: 15 MB por arquivo, 40 páginas e 16 milhões de pixels por página renderizada/imagem.
- O SQLite demo e os lançadores não substituem a configuração PostgreSQL de produção.
- Não houve publicação, implantação na VPS, atualização de anúncios ou extração das demais construtoras.

Referências de implementação: [pdfplumber](https://github.com/jsvine/pdfplumber),
[RapidOCR](https://github.com/RapidAI/RapidOCR) e
[SDK oficial MCP v1](https://py.sdk.modelcontextprotocol.io/v1/).
