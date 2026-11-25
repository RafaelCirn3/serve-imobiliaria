# Relatório de implementação — motor Drive V2

Implementação na branch `robo`, com alterações locais anteriores preservadas.
As referências utilizadas são `back-end/reports/mapa-fontes-20261124-203554.xlsx`
e `back-end/reports/mapa-filtros-20261124-210140.xlsx`. Os dois arquivos originais
foram lidos sem sobrescrita. O replay não consulta Drive, banco ou serviços de IA.
Não houve merge, publicação, atualização da VPS ou alteração de imóveis.

## Baseline reproduzida e resultados

Foram reproduzidos 16 fontes, 729 pastas, 5.822 arquivos e 91.621.068.239 bytes
originais conhecidos. A baseline filtrada contém 1.531 candidatos e
14.603.162.538 bytes, com 86 tabelas, 288 fachadas, 671 imagens de lazer e 486
internos. Os números abaixo vêm do replay do mesmo inventário, cruzado pela
combinação `(source_folder_id, drive_file_id)`.

| Indicador comparável | V1 | V2 | Variação |
|---|---:|---:|---:|
| Candidatos categorizados, incluindo revisão | 1.531 | 1.745 | +214 |
| Não candidatos | 4.291 | 4.077 | −214 |
| Tabelas candidatas | 86 | 92 | +6 |
| Fachada | 288 | 334 | +46 |
| Lazer | 671 | 806 | +135 |
| Internos | 486 | 513 | +27 |
| Oito tabelas MGA omitidas | 8 | 0 | −8 |
| Tabelas com identidade organizacional | 20 | 0 | −20 |
| Construtora não resolvida ou em revisão, nos candidatos | 478 | 585 | +107 |
| Volume candidato conhecido, bytes | 14.603.162.538 | 17.524.165.817 | +2.921.003.279 |

Foram recuperados 216 materiais e retirados dois documentos da seleção.
Entre os candidatos comuns às duas versões, houve oito mudanças de categoria,
615 mudanças na grafia/identidade de empreendimento e 86 mudanças na atribuição
empresarial. Mudança de nome inclui normalização; não significa 615 correções
homologadas de identidade. A execução final registrou 27,579 segundos até o
fechamento da auditoria e aproximadamente 27,7 segundos no terminal.
As oito tabelas MGA retornam como candidatas; os dois books/descritivos deixam
de ser tabelas. Isso explica o saldo de seis tabelas a mais. A redução de arquivos
passa de 73,70% para 70,03%, e a redução de bytes conhecidos de 84,06% para 80,87%.
Aumento da retenção não comprova aumento de acurácia.

A V2 separa três decisões principais: **1.098 SELECIONADO + 1.049 DESCARTADO +
3.675 REVISAO = 5.822**. A aba Arquivos continua mostrando candidatos
categorizados, inclusive os que necessitam revisão, para preservar a comparação
com V1. A aba Revisão é uma visão adicional; somar suas linhas às de Arquivos
duplicaria parte dos materiais. Todos os 5.822 têm uma decisão rastreável.

O aumento de identidades empresariais em revisão reflete a recuperação de materiais
e a atribuição mais conservadora em avulsos/catálogos mistos. Não foi reduzida a
fila de revisão por associação automática da empresa responsável pela pasta.

## Causas raiz e correções

| Déficit | Causa confirmada no código anterior | Alteração |
|---|---|---|
| Exclusão de fotos e tabelas MGA | Busca negativa no caminho completo abaixo da raiz | Hierarquia por IDs; segmentos estruturais; empreendimentos e contêineres mistos não propagam exclusão |
| Oito tabelas omitidas | `Plantas` nos sufixos de pastas de empreendimento | Recuperação validada pelos oito IDs reais e nome canônico correto |
| Books/descritivos tratados como tabela | Palavra `Tabela` no caminho composto e MIME PDF bastavam | Exclusão local de documentos técnicos/books; pasta comercial genérica não comprova tabela |
| Tabelas Alliance/DRX/Pirâmide com identidade organizacional | Profundidade fixa e tratamento incompleto de tabelas centralizadas | Estratégias de nome comercial, pasta abaixo da campanha e aliases exatos |
| Categorias semânticas conflitantes | Termos isolados e empate sem contexto | Expressões específicas por perfil, pasta inequívoca, tags e conflito explícito |
| Imagens ARC de sala de vídeo excluídas | `video` como palavra negativa global de arquivo | Exceção contextual do perfil comercial, mantendo vídeos reais fora pelo MIME |
| Imagens Bauten de cozinha/sala omitidas | Positivos exigiam expressões mais restritas | Aliases específicos do perfil Bauten, sem ampliar palavras das demais fontes |
| Descartes sem motivo individual | Arquivos removidos antes da exportação | Universo original preservado para auditoria, status, regras e evidências por arquivo |
| Confiança de categoria confundida com identidade | Uma pontuação e um rótulo de identidade | Três dimensões independentes, com evidência, regra, motivo e revisão |
| Uma fonte paralisava todas | Captura única de exceção em toda a lista | Isolamento por fonte, execução parcial, retry transitório e `--strict` opcional |
| Gravação sujeita a arquivo incompleto | Escrita diretamente no destino | Temporário no mesmo diretório e substituição atômica, inclusive no fechamento da auditoria |

Nas 20 associações organizacionais, 17 nomes de empreendimento foram recuperados.
Três arquivos da Pirâmide permanecem sem identidade: catálogos de imóveis de
Intermares para aluguel/venda e terreno em Praia Bela. Todos perderam a identidade
incorreta `TABELAS`; os três casos insuficientes foram para `UNKNOWN_PROJECT`,
sem inventar um nome canônico.

## Correções por fonte

| Fonte | Candidatos V1 | Candidatos V2 | Tratamento principal |
|---|---:|---:|---|
| BASE-01 Alliance | 195 | 213 | Tabelas centralizadas, nomes comerciais e pastas mistas |
| BASE-02 MGA | 8 | 173 | Sufixos compostos, oito tabelas, fotos recuperadas e dois documentos removidos |
| 01 ARC Space | 24 | 39 | Semântica comercial, sala de vídeo/podcast e construtora em revisão |
| 02 DRX | 302 | 302 | BLACK DRX é campanha; identidade abaixo dela, sem substituir tabelas convencionais |
| 03 Urban Prime | 11 | 11 | Raiz única; construtora continua desconhecida |
| 04 Pirâmide | 26 | 26 | Origem comercial separada de construtora; tabelas centralizadas e aliases |
| 05 MOSS | 32 | 32 | Categorias por pasta; térreo exige evidência adicional |
| 06 Compartilhado | 389 | 397 | Pastas mistas, datas/unidades fora da identidade e ausência de herança indiscriminada da Tropical |
| 07 TF | 101 | 101 | Segundo nível abaixo da etapa; nomes genéricos usam pasta categorizada |
| 08 Brascon | 16 | 16 | Avulsos e contexto de unidade, sem presumir a responsabilidade pelo imóvel |
| 09 Elevare | 14 | 14 | Chave compartilhada entre as três origens, com preservação das fontes |
| 10 Bauten | 262 | 270 | Aliases locais de internos, expressões específicas e marcação de vendido/histórico |
| 11 Externas | 20 | 20 | Somente candidatos complementares em revisão; não cria empreendimento |
| 12 Avulsos | 1 | 1 | Somente comercial e associação manual pendente |
| 13 Holanda Tambaú | 75 | 75 | Contexto dos finais preservado; hotel distinto do Bessa |
| 14 Holanda Bessa | 55 | 55 | Preferência por imagens comerciais e auditoria das cópias |

Todos os originais foram reavaliados. A lista de IDs dos **145 candidatos** da
auditoria anterior não foi fornecida; não se pode reproduzir exatamente essa
seleção apenas pelas contagens agregadas. A aba Recuperação auditada usa um
critério documentado de palavras explícitas dos perfis nas cinco fontes citadas:
**169 arquivos**, dos quais **132 viram candidatos**, **25 permanecem técnicos**
e **12 têm categoria ambígua**. Esse total não foi forçado para coincidir com 145.
As hipóteses de motivo V1 são reproduções das regras antigas, não um log V1 que
tenha sido observado na execução original.

## Arquitetura, regras e relatórios

O motor anterior foi evoluído: `SourceProfile.classify()` continua sendo o único
classificador. `annotate_inventory()` é compartilhado pelo scanner e pelo replay.
As configurações das 16 fontes são independentes e personalizáveis, com MIME,
categorias, palavras por arquivo/pasta, aliases, exceções, agrupamento, semântica,
confiança e catálogo canônico. `get_profile()` aplica defaults opcionais sem
sobrescrever os campos personalizados existentes.

Normalização preserva números de empreendimento/unidade e remove apenas
extensões, prefixos de cópia, numeração editorial, datas iniciais de entrega,
quantidade de unidades e sufixos descritivos pertinentes. O texto de busca dos
materiais mantém os termos técnicos necessários às exclusões contextuais.
São preservados originais, datas, MIME, contexto de torre/bloco/loja/final,
origem, fonte e evidências. Datas de modificação não validam a vigência comercial.

O relatório V2 contém as 11 abas solicitadas. Registra configurações efetivas,
SHA256 das regras e inventário, UUID da execução, tempos e falhas. Término e
duração são atualizados após gerar relatório, CSV e comparativo, antes do commit
atômico final da auditoria. IDs e checksums confirmam duplicidade de material;
nome/tamanho apenas levantam suspeitas. As **258 linhas de duplicidade** podem
representar evidências sobrepostas, não 258 cópias a remover. Todas as origens
permanecem catalogadas.

Formatos HEIF/HEIC/TIFF/PSD relevantes não são descartados por formato. São
sinalizados para conversão futura. Pillow e pillow-heif estão nas dependências e
foram encontrados no ambiente. Não houve download, conversão física ou extração
de conteúdo; a preferência de publicação usa somente metadados disponíveis.

Arquivos produzidos em `back-end/reports`:

- `mapa-filtros-v2.xlsx`: classificação, decisões, cobertura e auditoria.
- `comparativo-v1-v2.xlsx`: indicadores, mudanças individuais, fontes, recuperação e regressões P0.
- `mapa-filtros-v2-amostra.csv`: 246 arquivos estratificados para homologação humana.
- `replay-v2.log`, `tests-robot-v2.log`, `tests-v2-final.log`: evidência local de execução.

`reports/` permanece ignorado pelo Git. As referências originais foram preservadas.

## Arquivos de implementação

Criados nesta evolução V2:

- `back-end/apps/robot/mapping.py`: contexto estrutural, identidade, decisões e duplicidades.
- `back-end/apps/robot/inventory.py`: leitura offline e snapshot de regras.
- `back-end/apps/robot/audit_report.py`: auditoria XLSX e fechamento atômico dos tempos.
- `back-end/apps/robot/comparison.py`: diferenças por fonte/ID e regressões auditadas.
- `back-end/apps/robot/quality.py`: amostra e métricas homologadas.
- `back-end/apps/robot/management/commands/avaliar-filtros.py`: comando de avaliação humana.
- `back-end/apps/robot/migrations/0005_upgrade_filter_profiles_v2.py`: defaults aditivos, com snapshot independente.
- `back-end/apps/robot/fixtures/drive_regression_v1.json`: metadados reais de 144 arquivos das 16 fontes.
- `back-end/apps/robot/test_v2.py`: regressões, replay, auditoria, erros e métricas.
- Este relatório técnico.

Evoluídos: `profiles.py`, `profile_defaults.py`, `drive.py`, `report.py`, `sync.py`,
os comandos `mapear-fontes`/`mapear-filtros`, testes anteriores e os READMEs do
back-end e do robô. Os modelos previamente preparados DriveSource/DriveProject
foram reutilizados. Não há alteração destrutiva de schema. A sincronização mantém
as divulgações por fonte, resolve projetos canônicos quando há evidência e usa
identificador estável para tabelas de projetos diferentes na mesma pasta.
Nenhum intervalo do Celery Beat foi alterado.

## Testes e verificação

Baseline do robô antes da V2: **25 testes passaram**. Após a V2: **49 testes
passaram**. Cobertura inclui os oito IDs reais da MGA, as 20 associações
organizacionais, 16 perfis, estrutura TF, MIME comercial, imagens genéricas,
pastas mistas, semântica ARC, vendido, fontes complementares/comerciais,
identidades desconhecidas/conflitantes, três confianças, duplicidades, replay
determinístico, checksums, abas e rastreabilidade, contabilidade, migração
idempotente, retry seguro, escrita atômica e métricas após rótulo humano.

`check` e `makemigrations --check --dry-run` não indicaram problemas ou mudanças
de schema pendentes de geração. A migração de dados existe para aplicação no
ambiente de execução; o replay não a exige nem altera o banco.

A suíte completa executou **119 testes: 117 passaram e 2 terminaram em erro**:

1. `apps.banners.test_customization.CustomizationTests.test_image_upload_is_draft_until_saved`:
   `WinError 32`, arquivo aberto na limpeza do diretório temporário.
2. `apps.common.tests.ProductionMediaTests.test_cannot_escape_media_root_even_through_symlinks`:
   `WinError 1314`, processo sem privilégio para criar symlink no Windows.

Os dois erros foram reproduzidos isoladamente. Esses módulos não foram alterados
nesta tarefa. A suíte global não pode ser declarada integralmente verde neste
ambiente. Os XLSX foram conferidos programaticamente: estrutura, IDs, contagens,
decisões, hashes, conteúdo da auditoria, cabeçalhos e conservação do universo.
Não houve homologação visual nativa no Excel ou inspeção dos materiais reais.
A execução online com credenciais reais também não foi realizada nesta etapa;
isolamento de falhas e retries foram verificados com simulações nos testes.

## Reprodução

Dentro de `back-end`, com o ambiente virtual do projeto ativado:

```powershell
python manage.py test apps.robot --settings=config.test_settings
python manage.py check --settings=config.test_settings
python manage.py makemigrations --check --dry-run --settings=config.test_settings
python manage.py mapear-filtros --input-inventory reports/mapa-fontes-20261124-203554.xlsx --compare-to reports/mapa-filtros-20261124-210140.xlsx --output reports/mapa-filtros-v2.xlsx --comparison-output reports/comparativo-v1-v2.xlsx
```

Para repetir com o snapshot efetivo da configuração anterior, acrescente
`--rules-from reports/mapa-filtros-v2.xlsx` e use outro arquivo de saída.
Para leitura online, use `mapear-fontes`/`mapear-filtros` sem `--input-inventory`,
com credenciais de leitura configuradas. `--source` restringe a fonte, e
`--strict` mantém a política de falha imediata. As migrações podem ser aplicadas
no ambiente próprio com `python manage.py migrate`; não foram aplicadas em produção.

Após homologar a amostra CSV, preenchendo `categoria_humana`:

```powershell
python manage.py avaliar-filtros --amostra reports/mapa-filtros-v2-amostra.csv --output reports/metricas-homologadas.json
```

O comando não calcula métricas sem rótulos humanos. Categorias aceitas:
`tabela_precos`, `fachada`, `lazer`, `internos`, `DESCARTADO`. Precisão, recall,
F1 e matriz de confusão referem-se à amostra homologada; não são estimativas
automáticas da população a partir de uma amostra estratificada sem ponderação.

## Déficits resolvidos, parciais e pendências

Resolvidos por regressão: oito tabelas MGA recuperadas; dois documentos deixam
de ser tabelas; nenhuma das 20 tabelas mantém identidade organizacional;
exclusões contextuais; regras por fonte; confidências separadas; rastreabilidade;
replay; comparação; auditoria de duplicidades; isolamento de falhas e determinismo.

Parciais: três das 20 identidades ainda não podem ser resolvidas com metadados;
relação empresarial de ARC, Urban Prime, avulsos e parte dos catálogos mistos
continua para revisão; a lista exata de IDs dos 145 não estava disponível;
a acurácia global ainda não pode ser calculada; a suíte completa tem dois erros
de ambiente fora do robô.

Pendentes de fases futuras: homologação humana dos 246 casos, inspeção de imagens,
extração de tabelas/PDFs, disponibilidade real, vínculo definitivo entre unidades
e imagens, hash de conteúdo após download e hash perceptual. O inventário V1 não
contém checksums ou dimensões; esses campos permanecem desconhecidos no replay,
embora sejam coletados em novas consultas e preservados pelo novo inventário.
Nenhum material é automaticamente elegível para anúncio disponível nesta fase.
