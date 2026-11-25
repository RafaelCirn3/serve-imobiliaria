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
inicia a execução. Novas unidades entram como rascunhos, e anúncios publicados
mantêm seu status e preço. Alterações manuais e galerias manuais são preservadas.

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
O banco conserva 124 unidades publicadas e 140 rascunhos.

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
