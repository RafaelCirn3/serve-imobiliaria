# Importação SETAI Sandro Barros

O adaptador `SetaiTableParser` usa o mesmo extrator de documentos, serviço de
conferência, identidade de unidades e gerador de galerias da MGA. A seleção é
explícita: `inspect_table(..., developer_profile="setai")`. O perfil padrão
continua sendo `mga`; layouts desconhecidos não geram unidades SETAI.

## Fontes conferidas

- Origem comercial: Grupo Pirâmide, pasta `1oyftGZQJ2PljwIyhiipsc2kuFsyW02rg`.
- Tabela: `1OuEDeciuLh6aBWXMeqoJlprjlhWysRhB`, PDF sem extensão.
- Book: `1gxhEebYP9FVOlcIOs5-lhaKRT7i8DFFf`.
- Imagens: pasta `1915rnwsL46boW6deUaWK4Ti_Afl-Nfg8`.

O book identifica o empreendimento, os apartamentos, Cabo Branco/João Pessoa e
Grupo GP Exclusive/SETAI. O endereço numérico vem da tabela: Av. Cabo Branco,
2860. O book apresenta endereço sem número, por isso essa distinção permanece
na evidência. Materiais de outros empreendimentos da fonte não recebem SETAI
como responsável por associação à pasta comercial.

## Preços e revisão

A tabela apresenta preços de 27/04/2026, com rodapé de 07/05/2026. Não comprova
vigência ou disponibilidade atual. Cada unidade recebe os alertas
`VIGENCIA_NAO_CONFIRMADA` e `DISPONIBILIDADE_NAO_CONFIRMADA`, além da referência
ao book. A importação cria somente rascunhos e não substitui anúncios existentes.

| Unidades | Área total | Preço da tabela |
| --- | --- | --- |
| 22, 23 | 31,44 m² | R$ 638.800,00 |
| 363, 366, 367 | 22,95 m² | R$ 675.550,00 |
| 461 | 21,45 m² | R$ 696.400,00 |
| 544, 553 | 24,44 m² | R$ 840.960,00 |

O contador de linhas não é o número da unidade. A área é total conforme o
cabeçalho `AREA TOTAL DA U. H.`; a área privativa não é inferida. Plantas e book
não entram na galeria. Imagens de decorados são ilustrativas e não comprovam
mobília ou acabamento das unidades.

## Execução local

Com o inventário atualizado obtido por `scan_source()` e o PDF baixado:

```powershell
python manage.py robot-setai --arquivo reports/setai/tabela.pdf --inventory reports/setai/inventory-live.json
python manage.py robot-setai --arquivo reports/setai/tabela.pdf --inventory reports/setai/inventory-live.json --image-cache reports/setai/images --aplicar
```

O arquivo de inventário contém `source`, `folders` e `files`, no formato do
scanner compartilhado. A tabela deve coincidir com o MD5 do inventário. O cache
opcional de imagens usa `<drive_id>.jpg`, contendo os bytes originais, e também
é validado pelo MD5 antes do uso. Sem cache válido, usa o downloader existente.

Resultados ficam em `reports/setai/result.json`. A repetição reutiliza o
documento, as identidades e as galerias. Campos de cadastros revisados não são
reescritos. A transferência ao painel pode ser feita pela API de imóveis;
publicação continua dependendo da confirmação comercial, sem executar OCR na VPS.

```powershell
python manage.py test apps.robot --settings=config.test_settings
```
