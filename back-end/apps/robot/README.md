# Motor de fontes do Drive V2

Galerias dos imóveis importados: consulte
[`docs/robot-galerias.md`](../../../docs/robot-galerias.md). O comando
`vincular-imagens` aplica seleção sortida por categoria e vínculo específico de avulsos.

O MVP de extração MGA adiciona leitura de caracteres, OCR local quando necessário,
área de conferência e importação de rascunhos por CLI, API e MCP. Consulte
[`docs/robot-mga-mvp.md`](../../../docs/robot-mga-mvp.md) para execução e resultados.
No Windows, execute `back-end\mga-demo.cmd` a partir da raiz para demonstrar a
importação em SQLite isolado. O comando principal é `python manage.py robot-mga`.

O mapeamento interpreta metadados de 16 fontes. A extração seletiva e a importação
MGA são executadas pelo comando `robot-mga`, descrito no guia acima.
A origem comercial não comprova a construtora responsável.
As 13 empresas conhecidas e os perfis por `folder_id` ficam em
`profile_defaults.py`. `DriveSource.perfil` permite personalização no admin.
`get_profile()` completa campos opcionais de perfis V1 com defaults V2 sem
substituir personalizações. A migração 0005 persiste apenas defaults ausentes.

## Comandos

Execute em `back-end`, com o ambiente virtual ativado:

```powershell
python manage.py mapear-fontes
python manage.py mapear-filtros
python manage.py mapear-filtros --source ID_DA_PASTA --output reports/fonte.xlsx
```

`mapear-fontes` inventaria todas as pastas e arquivos das fontes ativas, inclusive
vazias e excluídos. Mantém as quatro abas e as colunas iniciais do inventário V1;
acrescenta metadados para auditoria/replay, checksums e dimensões quando disponíveis.
`mapear-filtros` mantém a hierarquia completa e separa arquivos categorizados,
descartados e pendências. Também grava uma amostra CSV para homologação humana.

Os dois comandos mostram tempo decorrido `[HH:MM:SS.d]`, duração por fonte,
contagens, preparação e gravação da planilha. `--verbosity 0` omite os marcos.
Os arquivos padrão são `reports/mapa-fontes-<data-hora>.xlsx` e
`reports/mapa-filtros-<data-hora>.xlsx`.

Uma fonte inacessível é registrada e as outras continuam. O resultado avisa
`EXECUÇÃO PARCIAL`. A aba Auditoria do mapa filtrado e a coluna de falha em Fontes
indicam as fontes não consultadas. As contagens parciais incluem somente o universo
efetivamente acessado. Use `--source` para reprocessar uma fonte ou `--strict` para
interromper na primeira falha sem gerar um relatório parcial. Se todas falharem,
o comando termina com erro e não grava XLSX. HTTP 429 e 500/502/503/504 têm até
três tentativas com espera de 1 e 2 segundos. Textos inesperados de erros externos
não são incluídos nos logs para evitar vazamento de credenciais.

## Replay e comparação

```powershell
python manage.py mapear-filtros --input-inventory reports/mapa-fontes-20261124-203554.xlsx --compare-to reports/mapa-filtros-20261124-210140.xlsx --output reports/mapa-filtros-v2.xlsx --comparison-output reports/comparativo-v1-v2.xlsx
```

O replay não consulta banco nem Drive e usa o mesmo `annotate_inventory()` do
scanner. Use o inventário **completo** como entrada; o mapa filtrado V1 é apenas
a baseline da comparação. A chave de comparação é `(source_folder_id, file_id)`.
Não é permitido sobrescrever a entrada ou a baseline por meio desses parâmetros.
`--rules-from reports/mapa-filtros-v2.xlsx` reutiliza o snapshot da aba Regras de
uma execução anterior. Sem essa opção, o replay usa os defaults da versão atual.

O resultado contém Resumo, Fontes, Pastas, Arquivos, Descartados, Revisão,
Empreendimentos, Cobertura, Duplicidades, Regras e Auditoria. A aba Arquivos
preserva as 18 colunas iniciais do V1 e acrescenta evidências e rastreabilidade.
A aba Auditoria registra UUID, SHA256 do inventário e das regras, versão do motor,
início, término, duração e falhas. Término/duração são atualizados depois da
planilha, amostra e comparativo, imediatamente antes do commit atômico final da
auditoria. O tempo do terminal inclui esse commit. XLSX é salvo por arquivo
temporário no mesmo diretório e substituição atômica; uma falha não destrói o
relatório anterior. Uma execução parcial é semanticamente diferente de uma
gravação incompleta.

## Decisões e confiança

Cada arquivo tem exatamente um status principal:

- `SELECIONADO`: categoria e identidades suficientes segundo os limiares.
- `DESCARTADO`: incompatibilidade de MIME ou exclusão contextual explícita.
- `REVISAO`: ambiguidade, ausência de evidência, identidade pendente ou validação comercial.

`SELECIONADO + DESCARTADO + REVISAO = originais`. A aba Arquivos é a visão de
**candidatos categorizados**, incluindo aqueles em revisão, para compatibilidade
com V1. Revisão é uma visão adicional: não some o número de linhas das abas como
se fossem partições. Resumo separa candidatos das três decisões principais.
Não candidatos podem incluir descartados e arquivos ainda sem categoria em revisão.

Há três objetos de confiança independentes, com pontuação, regra, evidências,
motivo e revisão: categoria, empreendimento e construtora. Os limiares padrão são
80/80/80 e são configuráveis em `thresholds`. Categoria: expressão específica 98,
nome e pasta 95, nome 90, pasta inequívoca 85, sem evidência 0. Empreendimento:
nome de perfil, pasta ou tabela centralizada 95; não resolvido 0. Construtora:
atribuição explícita de alta confiança 90, associação sujeita a confirmação 50,
desconhecida 0. São heurísticas, não probabilidades ou métricas de acurácia.
Toda tabela é candidata e exige validação de conteúdo, versão e vigência.

## Regras de negócio

`profiles.py` contém Company, ProjectIdentity, CategoryRule e SourceProfile.
`mapping.py` monta a hierarquia pelo vínculo entre IDs de pastas, preservando
nomes que contêm `/`. Os segmentos são raiz, organização, empreendimento,
categoria, subpasta e arquivo. Exclusões locais distinguem MIME, nome de arquivo
e pastas técnicas/promocionais. Pastas de empreendimento e contêineres mistos,
como `Imagens & Plantas`, não propagam exclusões indevidas. A árvore é sempre
inventariada; não há poda por palavra negativa de um ancestral.

Cada perfil admite categorias habilitadas, MIME, palavras de arquivo/pasta,
exceções, expressões específicas, aliases, regras centralizadas, profundidade,
limiares e prioridades. Sala de jogos/massagem e cozinha gourmet comum prevalecem
sobre termos genéricos; conflitos equivalentes permanecem ambíguos. Arquivo
genérico em pasta inequívoca é classificável; imagem genérica em pasta genérica
vai para análise visual futura. ARC aceita salas de vídeo/podcast como ambientes.
Bauten possui aliases próprios para cozinha/sala/quartos/flat, sem estender esses
positivos às demais fontes.

Alliance associa tabelas centralizadas por nome comercial normalizado; DRX ignora
a campanha BLACK DRX como identidade; Pirâmide usa nomes das tabelas e aliases
explícitos de seus materiais. Rótulos organizacionais não viram empreendimentos.
Nome comercial insuficiente permanece não resolvido. MGA remove sufixos compostos;
TF agrupa abaixo da etapa. Fontes únicas usam a raiz. Datas e quantidade de unidades
são removidas apenas da identidade; Mondo 2, Farol 137 e números de unidades são
preservados. Originais e contexto de torre, bloco, loja e finais continuam no relatório.

O catálogo configurável `canonical_projects` admite aliases exatos, empresas e
referências de fontes. Elevare usa a mesma chave nas três origens. Os hotéis
Holanda são distintos. Aliases conflitantes geram revisão; não há fusão por
similaridade textual aproximada. Origem, construtora, incorporadora, empreendimento,
contexto de unidade e fonte são campos separados. Pirâmide/compartilhado/avulsos
não herdam indiscriminadamente a construtora da pasta.

Vendido, esgotado e histórico são catalogados, com bloqueio de elegibilidade
automática. Na fase atual nenhum material autoriza publicação. Tabelas
promocionais, convencionais e históricas são preservadas separadamente, com
vigência não confirmada. Ausência no Drive não significa unidade vendida.

Deduplicação usa ID e checksum informado pelo Drive; nome+tamanho sinaliza apenas
suspeita. Todas as origens são preservadas. A referência preferencial considera
metadados de formato/resolução/promoção, sem certificar qualidade visual.
HEIF, HEIC, TIFF e PSD relevantes continuam candidatos, com sinalização de conversão.
Pillow e pillow-heif já são dependências. Hash de arquivo baixado e hash perceptual
ficam para as etapas futuras de processamento físico.

## Homologação e testes

Preencha `categoria_humana` no CSV de amostra com `tabela_precos`, `fachada`,
`lazer`, `internos` ou `DESCARTADO`. Não altere fonte e ID original.

```powershell
python manage.py avaliar-filtros --amostra reports/mapa-filtros-v2-amostra.csv --output reports/metricas-homologadas.json
python manage.py test apps.robot --settings=config.test_settings
python manage.py makemigrations --check --dry-run --settings=config.test_settings
```

O cálculo recusa uma amostra totalmente sem rótulos. A matriz inclui abstenções
`REVISAO`; métricas referem-se à amostra estratificada homologada, não à população
inteira. Retenção e recuperação de regressões não substituem precisão/recall/F1.

As fixtures de regressão usam metadados de 144 arquivos reais, cobrindo as 16
fontes, sem credenciais. O teste das oito tabelas usa seus IDs reais. O agendamento
de 24 horas do Celery Beat é preservado; o replay e os comandos de mapeamento não
alteram imóveis nem divulgações. A sincronização mantém seus registros pendentes,
isola falhas de consulta e não cria identidade canônica para fontes complementares
ou exclusivamente comerciais.
