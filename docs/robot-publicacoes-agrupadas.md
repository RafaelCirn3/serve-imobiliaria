# Publicações por empreendimento e torre

O robô mantém cada unidade no cadastro administrativo, com preço exato,
proveniência da tabela e galeria. O catálogo público reúne as unidades publicadas
pela combinação de construtora, empreendimento, cidade, torre, finalidade,
tipo, quantidade de quartos/suítes e área, preservando a natureza da área.
Áreas diferentes formam anúncios diferentes, mesmo na mesma torre.
Venda e locação permanecem separadas. Sem torre identificada, forma-se um grupo
sem torre, sem atribuir A, B ou C por suposição. Avulsos continuam individuais.

O agrupamento é ativado nas novas importações de empreendimentos pelo robô.
Cadastros manuais continuam individuais até a ativação de `agrupar_publicacao`.
As chaves usam nomes normalizados e independem da pasta de origem. A consulta
aplica os filtros às unidades antes de escolher uma publicação por grupo;
rascunhos, vendidos, alugados e inativos não entram no grupo público.

## Preço e ficha pública

`valor` permanece exato no cadastro. Na resposta pública agrupada, ele contém
o menor preço exato entre as unidades publicadas; `valor_exibicao` contém esse
mínimo arredondado para baixo na primeira casa significativa:

| Menor preço real | Chamada pública |
|---:|---|
| R$ 2.122.036,00 | A partir de: R$ 2.000.000 |
| R$ 2.495.965,19 | A partir de: R$ 2.000.000 |
| R$ 527.286,81 | A partir de: R$ 500.000 |
| R$ 999.999,99 | A partir de: R$ 900.000 |

O arredondamento é de apresentação e não altera preços, filtros ou condições
comerciais. A ficha mostra opções com os preços exatos. Dados de quartos,
vagas e áreas que variam entre unidades não são apresentados como se fossem
iguais em todo o empreendimento. Tipologias diferentes aparecem individualmente
na tabela de unidades.

Listagem, destaques, busca e mapa exibem um card por grupo. O detalhe público
aceita os slugs anteriores das unidades publicadas e resolve o mesmo grupo.
O slug público é derivado do empreendimento, tipologia, área e chave do grupo,
sem revelar o número da unidade ou o andar. A identificação interna do anúncio
usa a unidade publicada mais antiga; os registros individuais continuam no banco.

Novos campos públicos: `agrupado`, `quantidade_unidades`, `valor_exibicao`.
`GET /api/imoveis/<slug>/unidades/` lista somente unidades publicadas do grupo,
com preço exato em texto decimal, torre, tipologia, área e vagas, sem unidade
ou andar. Opções idênticas são consolidadas. A API administrativa mantém
unidade, andar, tipologia original, registro de incorporação e status individuais.

## Correção da captura de preços MGA

O parser MGA 1.4 recupera cabeçalhos mesclados antes de recorrer às coordenadas
das palavras. Isso evita separar `R$ 2 .122.036,00` em colunas diferentes no
Elevare. Valores positivos abaixo de R$ 1.000 em uma tabela de venda ficam
marcados com `PRECO_SUSPEITO` e exigem revisão explícita antes da importação.
Essa faixa é uma regra de triagem, não uma inferência do preço correto.

O comando abaixo compara os candidatos com os PDFs de mesmo SHA256. Sem
`--aplicar`, apenas gera a prévia. Com a opção, corrige somente preços de
candidatos não importados e não revisados, com identidade inequívoca; preserva
anúncios, alterações manuais e histórico. A execução mostra tempo e marcos.

```powershell
docker compose exec -T api python manage.py corrigir-precos-mga
docker compose exec -T api python manage.py corrigir-precos-mga --aplicar
```

Para cadastros já importados pelo robô:

```powershell
docker compose exec -T api python manage.py agrupar-publicacoes
docker compose exec -T api python manage.py agrupar-publicacoes --aplicar
docker compose exec -T api python manage.py vincular-imagens --aplicar
```

O agrupamento não publica candidatos e não altera os status existentes. A
migrações 0011 a 0013 de properties devem ser aplicadas antes dos comandos.

## Rodapé e preparação do Elevare

O extrator lê endereço, bairro, previsão de entrega e registro de incorporação
no documento inteiro e aplica os dados às unidades de todas as páginas. Não
propaga o rodapé de um imóvel para outros imóveis de tabelas de avulsos.
Conserva página, método e trecho original como evidência. Andares em células
mescladas da grade são recuperados sem inferir o andar pelo número da unidade.

`Dez/31` é salvo como `2031-12`, sem inventar um dia. Uma previsão futura gera
`em_construcao`, separado do tipo `apartamento`. Depois do mês previsto, a
situação é `entrega_a_confirmar`, sem declarar automaticamente que a obra acabou.

No Elevare, o rodapé informa Rua Josita Almeida, 373, Altiplano Cabo Branco,
registro R-4-170.506 e dezembro/2031. A cidade foi confirmada como João Pessoa
por [documento da Câmara Municipal](https://sapl.joaopessoa.pb.leg.br/media/sapl/public/materialegislativa/2023/170792/_req_-_recolhimento_de_residuos_-_rua_josita_almeida-_altiplano.docx.pdf)
e fornecida em contexto explícito, sem atribuir João Pessoa a qualquer bairro.

```powershell
docker compose exec -T api python manage.py preparar-mga --empreendimento Elevare --contexto apps/robot/fixtures/mga/elevare-context.json --aplicar
```

O comando usa os PDFs locais com o SHA256 original, atualiza os candidatos não
revisados e cria somente rascunhos válidos. Preserva preços de anúncios e
revisões manuais. As imagens são vinculadas por padrão nessa preparação;
somente `--sem-imagens` adia essa etapa explicitamente. Rascunhos de empreendimentos
podem ser salvos com localização pendente; a publicação exige confirmação.

## Diversidade das galerias

O plano 2.0 compara sequências e capas de imóveis com construtoras em comum,
incluindo planos reservados enquanto as imagens são baixadas. Ele prioriza uma
sequência diferente, depois capas menos repetidas e menos posições iguais.
O plano é persistido: repetir o comando não sorteia uma galeria nova.

Continuam válidos os limites: até duas fachadas primeiro, quatro imagens de
lazer e três de internos. O acervo permite de seis a nove imagens quando há
material suficiente. As imagens continuam limitadas ao empreendimento, torre
e unidade elegíveis; avulsos usam somente o próprio acervo. Imagens manuais
são preservadas. Quando o acervo não permite outra sequência, o resultado
registra `ACERVO_SEM_VARIACAO_DE_SEQUENCIA`, sem usar material de outro imóvel.

## Aplicação local de 25/11/2026

- Corrigidos 53 preços do Elevare nos candidatos do PostgreSQL, com histórico.
- Reconferidas 270 linhas contra as grades dos nove PDFs: nenhuma divergência
  de preço ou área após a correção; 48 linhas Elevare seguem sem preço na fonte.
- Repetição da correção: zero mudanças, bloqueios ou erros.
- Os dois Makai publicados têm áreas diferentes e formam dois anúncios,
  cada um com chamada de R$ 2.000.000. Os preços reais permanecem
  R$ 2.495.965,19 e R$ 2.894.367,60.
- Galerias Makai com seis imagens e sequências/capas diferentes.
- Elevare: 122 unidades cadastradas como rascunhos em seis grupos por torre,
  suítes e área; 48 linhas sem preço continuam pendentes. Repetir a preparação
  cria zero unidades e reconhece 122 existentes. Todas têm endereço, previsão
  de entrega e metadados administrativos. Após validação e solicitação do
  operador, as 122 unidades foram publicadas no localhost, em seis anúncios.
  Os dois anúncios de maior valor por torre (350,07 m² na A e 262,43 m² na B)
  estão em destaque, ordenados por preço decrescente. Com os dois Makai, o
  catálogo local tem oito anúncios. As 48 linhas sem preço permanecem pendentes.
- As 122 unidades Elevare receberam 760 fotos do acervo do empreendimento,
  com 122 sequências distintas. Nenhuma unidade ficou sem galeria. A conferência
  validou limites, ordem, capa, origem e existência dos arquivos; amostras dos
  16 arquivos de origem responderam HTTP 200. A repetição preservou todos os
  IDs e sequências sem novos downloads. Interiores sem identificação de planta
  continuam como imagens ilustrativas do empreendimento, pendentes de vistoria.
- O Mondo 2 foi confirmado pelo operador como o mesmo Mondo, no Bessa.
  A sincronização descrita em `robot-mga-sincronizacao.md` reúne as duas tabelas
  na mesma identidade e permite compartilhar seu acervo de imagens.

## Endereço, região, CEP e localização

O endereço original permanece em `endereco`. O organizador separa `logradouro`,
`numero`, `bairro`, `cidade` e `uf`. Altiplano, Cabo Branco, Jardim Oceania,
Tambaú, Brisamar e Bessa estão cadastrados como regiões de João Pessoa, conforme
o [mapa municipal de bairros](https://www.joaopessoa.pb.gov.br/servico/maparegioes/).
Quando o campo de bairro contém mais de um nome reconhecido, vale o primeiro
na ordem do texto: `Altiplano Cabo Branco` resulta em `Altiplano`, enquanto
`Cabo Branco / Altiplano` resulta em `Cabo Branco`. Isso também vale nas respostas
de CEP, impedindo que a consulta recoloque o nome composto no formulário.

O CEP é obtido no ViaCEP por rua e cidade, validando o nome da rua, bairro e UF.
Só é preenchido automaticamente quando há um único CEP correspondente. Os
casos ambíguos ou indisponíveis ficam pendentes, sem escolher arbitrariamente.
As coordenadas vêm do geocodificador e permanecem aproximadas. Coordenadas
existentes são preservadas pelo lote; o botão explícito no admin recalcula.
Consultas são reutilizadas pelo cache para unidades no mesmo endereço.

No admin, o botão “Organizar endereço, CEP e localização” preenche os campos
para conferência e salvamento. O endpoint autenticado correspondente é
`POST /api/localizacao/organizar/`. Novos cadastros do robô organizam os campos
e resolvem CEP/coordenadas após a importação, registrando evidências e pendências.

```powershell
docker compose exec -T api python manage.py organizar-enderecos --empreendimento Elevare --area-total --aplicar
```

Por decisão explícita do operador, a coluna genérica de área do Elevare passa
a preencher `area_total`, mantendo também `area_informada` para rastreabilidade.
A regra foi salva no parser por empreendimento e no contexto do Elevare;
não altera a natureza da área de outros empreendimentos por suposição.

No localhost, os 122 imóveis Elevare ficaram com Rua Josita Almeida, número
373, bairro/região Altiplano, João Pessoa/PB, CEP 58046-490 e coordenadas
aproximadas -7.1383523, -34.8267168. Todos têm área total igual à informada;
as 760 fotos e os seis grupos foram preservados, sem alterar status de publicação.
