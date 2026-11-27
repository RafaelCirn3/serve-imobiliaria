# ICON / MOSS: cobertura e operação do robô

Conferência das fontes fornecidas em 27/11/2026. Este escopo é o material
compartilhado do MOSS, não o estoque integral da ICON.

## Resultado do inventário completo

Fonte: pasta `1xwjaaLOZVu3fstFeS2XNAYOwNtIRFMjr`, `MOSS @padraoicon`.

| Item | Resultado |
| --- | ---: |
| Pastas, incluindo a raiz | 11 |
| Arquivos inventariados | 63 |
| Tabelas comerciais | 1 |
| Imagens disponíveis no Drive | 56 |
| Imagens categorizadas para galerias | 49 |
| Fachadas | 9 |
| Áreas comuns/lazer | 34 |
| Interiores ilustrativos | 6 |
| Arquivos excluídos com motivo | 13 |
| Arquivos sem enquadramento | 0 |

As 13 exclusões incluem três vistas de entorno sem fachada identificável,
quatro imagens de subsolo, três PDFs de book/plantas/descritivo, uma revista e
dois arquivos em formatos fora das categorias de importação. Exclusão da
galeria não implica que o material não tenha utilidade documental.

Os 63 arquivos se dividem em 49 imagens selecionadas, uma tabela em revisão
comercial e 13 excluídos. As decisões visuais complementares estão em
`apps/robot/asset_reviews.py`, vinculadas ao ID e MD5 do arquivo. Se o conteúdo
mudar, a aprovação anterior não é aplicada.

## Extração conferida

Tabela: `[MOSS] icon Tabela Novembro26.pdf`, ID
`1XIQOUsqnVajYGY1GjqOz-PIGkZ4I835B`, quatro páginas, novembro/2026.
Book: `[MOSS] icon BOOK.pdf`, ID `1SgD0mYllMftdiUiTA5CTQIkV15rslMR7`.

- O cabeçalho declara 21 unidades disponíveis e uma indisponível.
- Foram extraídas as 22 unidades: 21 disponíveis e a unidade 205 reservada.
- A reconciliação das contagens é obrigatória antes de gravar cadastros.
- As 21 disponíveis geraram rascunhos, com 144 fotos no total.
- A 205 fica registrada como candidata indisponível, sem criar oferta imobiliária.
- Nenhuma unidade da tabela ficou sem extração.

Preço mínimo das disponíveis: R$ 446.730,02 (1002). Máximo: R$ 698.807,78 (405).
Áreas privativa e total são preservadas separadamente, mesmo quando iguais.
Todas as disponíveis declaram um dormitório e uma suíte. Entrega prevista:
setembro/2029. Incorporação conforme tabela: `5-162.376`.

O book comprova ICON, studios, Cabo Branco/João Pessoa e Av. Monsenhor Odilon
Coutinho. Não se inventa número predial. As imagens são ilustrativas do
empreendimento; não comprovam mobília ou acabamento de uma unidade específica.

As 21 unidades atendem aos critérios estruturais de cadastro e galeria. A
política compartilhada mantém `VIGENCIA_NAO_CONFIRMADA`: zero foram liberadas
para publicação automática nesta execução. Disponibilidade declarada na tabela
e confirmação comercial atual são registradas separadamente.

## Motor compartilhado

`extraction/common.py` contém tipos, normalização monetária e montagem da
unidade. MGA, SETAI e o layout DWV usam esse núcleo. `extraction/dwv.py` trata
cartões comerciais, cabeçalhos de andar, parcelas e continuação entre páginas;
`IconTableParser` configura a origem ICON. `extraction/registry.py` seleciona
explicitamente o adaptador.

`developer_pipeline.py` compartilha a verificação de origem e checksum,
extração, conferência de cobertura, identidade, rascunhos, cache e galerias entre
ICON e SETAI. Os comandos `robot-icon` e `robot-setai` são entradas finas para
`robot-fonte`. A rotina de sincronização MGA e sua política de publicação
preservam o comportamento anterior.

```powershell
python manage.py robot-icon --arquivo reports/icon/1XIQOUsqnVajYGY1GjqOz-PIGkZ4I835B.pdf --inventory reports/icon/inventory-live.json --image-cache reports/icon/images
python manage.py robot-icon --arquivo reports/icon/1XIQOUsqnVajYGY1GjqOz-PIGkZ4I835B.pdf --inventory reports/icon/inventory-live.json --image-cache reports/icon/images --aplicar
```

O comando genérico equivalente usa `robot-fonte --perfil icon`. A execução é
local, sobre um inventário completo obtido pelo scanner existente. Não foi
configurado novo agendamento automático nem implantado o código do adaptador na
VPS; a produção recebe os cadastros e as fotos pela API.

Relatórios locais ficam em `back-end/reports/icon/`: `inventory-live.json`,
`result.json`, `repeat.json`, `three-developers-audit.json`,
`transfer-production.json` e `transfer-production-verification.json`.
