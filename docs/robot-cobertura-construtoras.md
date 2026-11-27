# Cobertura de três construtoras

Conferência em 27/11/2026, restrita às fontes fornecidas e tabelas processadas.

É correto afirmar: **MGA, SETAI e ICON possuem adaptadores de extração mapeados
e testados para os materiais fornecidos, com importação de rascunhos e vínculo
de galerias.** Isso não equivale à cobertura do estoque integral das empresas
nem à autorização de publicação automática de todos os registros.

| Construtora | Tabelas processadas | Linhas/unidades mapeadas | Imóveis cadastrados | Não convertidas em cadastro | Publicados dessas importações |
| --- | ---: | ---: | ---: | ---: | ---: |
| MGA | 10 | 313 | 264 | 49 | 223 |
| SETAI | 1 | 8 | 8 | 0 | 0 |
| ICON / MOSS | 1 | 22 | 21 | 1 reservada | 0 |

Na MGA, as 49 linhas sem imóvel vinculado são 48 linhas do Elevare com alerta de
preço pendente e uma do Soleil com alertas de tipologia/localização. Elas
permanecem auditáveis; não são falhas de descoberta de arquivo. Dos 264 imóveis
importados, 41 permanecem rascunhos.

Na SETAI, os oito cadastros estão como rascunhos. A tabela é de abril/maio de
2026; preço/disponibilidade e dormitórios/tipologia precisam de conferência.
Há um anúncio SETAI anterior publicado, fora dessas oito importações e sem
unidade identificada; não foi somado aos resultados do robô.

Na ICON, foram inventariadas todas as 11 pastas e os 63 arquivos da fonte MOSS.
As 22 unidades do PDF foram recuperadas e reconciliadas com o cabeçalho:
21 disponíveis e uma reservada. As 21 disponíveis foram preparadas como
rascunhos com 144 fotos. A unidade 205 reservada não gera anúncio.
Os 21 cadastros atendem aos critérios estruturais; confirmação comercial da
vigência ainda impede a liberação automática para publicação.

Os registros anteriores de produção foram preservados. A transferência não
executa OCR nem interpretação de PDF na VPS.

Detalhes: [SETAI](robot-setai.md), [ICON](robot-icon.md). Evidência completa e
contagens de banco: `back-end/reports/icon/three-developers-audit.json`.
