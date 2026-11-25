# Sincronização MGA

## Regras confirmadas pelo operador

- Bananeiras usa o bairro Centro no cadastro comercial. O endereço original
  da tabela permanece preservado. Esta é uma regra da aplicação.
- Avulsos sem finalidade explícita: preço positivo inferior a R$ 100.000
  recebe Aluguel; a partir desse valor recebe Venda. A finalidade explícita
  prevalece. Preço ausente ou inválido continua pendente.
- MONDO 2 e Mondo são o mesmo empreendimento, em João Pessoa, bairro Bessa.
  Ambos usam identidade Mondo e compartilham imagens desse empreendimento.
  As salas de locação mantêm Aluguel. Dados de unidades distintas são mantidos.
- Colunas explicitamente chamadas Área Total preenchem `area_total`.
  Outras áreas genéricas não são classificadas por suposição; permanece a
  decisão anterior de usar a área do Elevare como total.

## Executar pela aplicação

```powershell
docker compose exec -T api python manage.py sincronizar-mga --aplicar
```

Sem `--aplicar`, inspeciona as tabelas sem importar imóveis ou vincular fotos.
O inventário consulta as quatro fontes ativas relacionadas à MGA, conservando
a identificação da construtora por empreendimento nos catálogos mistos.
O terminal mostra tempo decorrido e marcos de fonte, tabela, unidade e imagem.

Para retomar com o inventário da execução, sem repetir a consulta das pastas:

```powershell
docker compose exec -T api python manage.py sincronizar-mga --snapshot reports/mga/sync-inventory-live.json --aplicar
```

O relatório é salvo após cada unidade em `back-end/reports/mga/sync-result.json`.
O inventário salvo representa o momento da consulta; para buscar mudanças
posteriores, execute novamente sem `--snapshot`.
O acompanhamento autenticado está disponível em
`GET /api/admin/robot/mga/extracoes/sincronizacao/` e na ferramenta MCP
`mga_consultar_sincronizacao`. Esses recursos consultam o andamento; o comando
inicia a execução. Novas unidades começam como rascunhos e, após a montagem
da galeria e resolução de endereço, são publicadas automaticamente quando
atendem ao padrão abaixo. Anúncios publicados mantêm seu status e preço.
Alterações manuais e galerias manuais são preservadas.

## Publicação automática pelo padrão aprovado

A classe `MGAPublicationPolicy` centraliza a versão `mga-publication-1.0`.
O padrão foi conferido contra os 223 imóveis já aprovados: todos atendem.
É executado na sincronização completa e após a montagem das imagens nas
importações por CLI, API e MCP. A decisão e suas pendências ficam na evidência
do candidato (`publication`) e no relatório de sincronização por unidade.

São necessários: origem MGA, dados da tabela válidos, preço positivo,
cidade/bairro/logradouro, área positiva e quartos ou suítes para apartamentos.
Avisos de OCR, preço suspeito, indisponibilidade, duplicidade ou conflitos
exigem revisão explícita do candidato. CEP e coordenadas não são inventados
nem bloqueiam por si só a divulgação, conforme o catálogo aprovado.

A galeria precisa ter ao menos seis fotos locais existentes, até duas fachadas,
quatro de lazer e três de interiores, sem ultrapassar os limites por categoria.
Isso permite até nove fotos. A ordem é Fachada → Lazer → Internos, com uma única
capa, na primeira foto de fachada. A inspeção é de metadados e arquivos;
o marcador de vistoria visual pendente é preservado.

Os rascunhos incompletos permanecem em revisão. Imóveis inativos, vendidos,
alugados ou já publicados não têm o status alterado por essa política.
O agrupamento, preços exatos, chamada arredondada “a partir de”, privacidade
de unidade/andar e destaques existentes continuam seguindo suas regras.
A publicação automática não marca todo imóvel como destaque.

Para conferir ou aplicar o padrão nos rascunhos já importados:

```powershell
docker compose exec -T api python manage.py publicar-mga
docker compose exec -T api python manage.py publicar-mga --aplicar
```

Em 25/11/2026, a aplicação da política manteve os 223 imóveis publicados e
os 41 rascunhos pendentes. O relatório fica em
`back-end/reports/mga/publication-policy.json`.

O fluxo busca texto nativo antes de OCR, reutiliza extrações por hash,
identifica unidades entre versões e ignora cópias idênticas das tabelas.
As galerias respeitam empreendimento, torre e unidade quando identificados,
ordem Fachada → Lazer → Internos e limites de 2/4/3 imagens por categoria.
Avulsos utilizam exclusivamente seu próprio acervo. Imagens ilustrativas
seguem marcadas para vistoria; não há inspeção visual automática.

## Resultado local em 25/11/2026

Foram consultados 2.397 arquivos em quatro fontes. Das 12 referências de tabela,
duas eram cópias: dez documentos distintos totalizaram 313 linhas candidatas.
Há 264 unidades importadas, com 1.548 vínculos de fotos e todos os arquivos
locais conferidos. A repetição criou zero imóveis, reconheceu 264 existentes
e terminou sem erros de processamento ou download.

Mondo reúne 63 unidades, todas com bairro Bessa e logradouro preenchido.
Após a aprovação solicitada pelo operador, o banco conserva 223 unidades
publicadas (91 anúncios agrupados) e 41 rascunhos.

Pendências que impedem considerar todo o acervo pronto para divulgação:

- 48 linhas do Elevare não possuem preço na própria tabela.
- Uma linha do Soleil apresenta conflito de tipologia e exige revisão.
- Lumini: 27 galerias com quatro fotos; Soho: sete com cinco fotos.
  Fotos repetidas são descartadas por conteúdo e não completam a quantidade.
- Brisas do Atlântico: quatro fotos elegíveis, sem fachada identificada.
- Alteza, em Bananeiras/Centro: há plantas e materiais técnicos, sem fotos
  elegíveis do próprio lote. Não são usadas imagens de outros imóveis.
- CEP, coordenadas e classificação da área permanecem sujeitos à confirmação
  onde a tabela ou os serviços de localização não oferecem evidência suficiente.

O detalhe por unidade está em `back-end/reports/mga/final-audit.json`.
