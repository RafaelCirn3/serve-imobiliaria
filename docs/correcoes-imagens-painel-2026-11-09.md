# SERVE — imagens e experiência administrativa

Data: 09/11/2026. Base: `bd38c4c6393fce636d02a5b7abce38cc5b9d63fe` na Main.

## Proposta implementada

O painel foi reorganizado para uma pessoa que administra imóveis, com linguagem direta e imagens como referência principal. A paleta mantém o carvão e o branco da SERVE: navegação escura, área de trabalho clara, cartões brancos, bordas discretas e cores funcionais para publicação, preenchimento e erros. O site público conserva sua identidade visual.

### Encontrar e administrar imóveis

- A listagem passa de uma tabela apenas textual para cartões com foto de capa, quantidade de fotos, preço, localização, finalidade e status.
- Cada cartão oferece Editar imóvel, Ver no site quando publicado e Inativar. A inativação mantém o cadastro e pede confirmação.
- Busca com rótulos, filtros por tipo e status, paginação, quantidade de resultados e mensagens de carregamento, erro e lista vazia.
- O painel inicial mostra fotos dos imóveis recentes, contatos, totais de cadastros/publicados/rascunhos e aviso sobre imóveis sem fotos.
- As vitrines de imóveis também mostram miniaturas durante a seleção, evitando depender apenas do título.

### Cadastrar e editar com orientação

- Etapas numeradas, etapa atual destacada e indicação textual de preenchimento/pendências.
- Barra com a contagem de campos obrigatórios preenchidos, sem transformar os campos opcionais em exigências.
- Cada campo mostra Obrigatório, Opcional, Preenchido ou o erro correspondente. A indicação combina texto e cor.
- Respostas de validação da API também marcam o campo e abrem a etapa que precisa de atenção.
- Resumo com foto, título, localização, status e contagem de fotos permanece visível durante a edição. No celular, aparece acima do formulário.
- Distinção entre fotos salvas e arquivos aguardando envio, com acesso direto a Gerenciar fotos.
- Indicação de alterações não salvas e checklist sobre informações obrigatórias, fotos recomendadas e publicação.
- Navegação entre etapas e acesso de volta à lista. Mantida a preservação dos arquivos entre etapas e dos rascunhos da sessão.
- Menu móvel compacto, campos legíveis sem zoom automático e nomes de etapas sem corte em telas estreitas.

### Demais ferramentas

O tratamento visual é compartilhado pelos formulários de textos, carrosséis, regiões e contatos. A edição de textos foi dividida por seções. Imagens principais e regiões passam a ter prévia antes de salvar, marcação de campos obrigatórios e feedback de erro/salvamento. O nome técnico “Hero” foi substituído por linguagem de uso no painel.

## Erros corrigidos e evidências

| Erro | Causa identificada | Correção |
| --- | --- | --- |
| Fotos quebradas em produção | A configuração encaminha `/media/` ao backend, mas `static(settings.MEDIA_URL, ...)` só registra essa rota com `DEBUG=True`. Os testes anteriores não verificavam a leitura dos arquivos em produção. | Rota explícita para imagens, com resposta binária e MIME correto, disponível com `DEBUG=False`. Validada com Gunicorn e leitura/decodificação real das imagens. Compatível com o proxy e o volume de mídia existentes. |
| Possível bloqueio por URL HTTP ou origem antiga | Os endereços absolutos podem refletir uma configuração anterior do proxy. | URLs de `/media/` são normalizadas para a origem da API usada pelo site, evitando mídia HTTP em página HTTPS e dependência de hosts antigos. |
| Galeria vazia com ícones quebrados | Os elementos de imagem não tinham estados de carregamento e falha. | Componente compartilhado com carregamento, foto e mensagem explícita de indisponibilidade. Imóveis sem foto não recebem uma fotografia de outro imóvel como substituição. |
| Imagens ocultas durante a administração | Listagem e painel não exibiam fotos; na edição elas ficavam restritas a uma etapa. | Fotos grandes na listagem, miniaturas no painel/vitrines e prévia persistente na edição. |
| Capa escolhida não era respeitada no detalhe público | A galeria inicial usava a primeira imagem do cadastro. | A abertura do detalhe prioriza a foto marcada como capa. |
| Contadores incorretos acima de uma página de dados | Os totais eram calculados pelo tamanho da primeira página retornada. | Resumo administrativo agregado no backend; teste com 13 imóveis e múltiplas fotos garante totais distintos corretos. |
| Cadastros além da primeira página sem navegação | A interface não oferecia paginação. | Navegação Anterior/Próxima com preservação dos filtros. |
| Falhas de capa/exclusão sem retorno claro | As operações não tratavam erro nem bloqueavam cliques repetidos. | Estado de operação, confirmação de exclusão e mensagens de sucesso/falha. A capa do resumo atualiza após confirmação da API. |
| Preenchimento pouco compreensível | Labels e aviso geral não mostravam o estado de cada campo. | Indicadores por campo, progresso e erros da API junto dos campos. |
| Formulários auxiliares permitiam envio sem orientação | Faltavam validação visual, prévia e tratamento de falhas em imagens principais/regiões. | Validação antes do envio, prévia da seleção e manutenção dos dados após falha. |
| Mapa poderia abrir com dimensões incorretas ao alternar etapas | O contêiner pode mudar de oculto para visível depois da criação do mapa. | Observação das dimensões e atualização do mapa quando a área muda. |

A rota pública de imagens rejeita caminhos fora do diretório de mídia, links simbólicos para fora dele, diretórios, extensões não permitidas e métodos de escrita. A resposta inclui `nosniff` e cache. Não foi necessário ativar `DEBUG` em produção nem alterar dados existentes.

## Verificações

- **55 testes Django aprovados**, incluindo entrega de bytes de imagem com `DEBUG=False`, HEAD, arquivo ausente, proteção de caminhos, totais do catálogo e diagnóstico de arquivos ausentes.
- **Build Angular de produção aprovado**, sem avisos do compilador Angular.
- Verificações de sistema, migrações e integridade do diff sem pendências.
- Regressão com **Chromium desktop e WebKit móvel** usando frontend de produção, **Gunicorn, `DEBUG=False`, API e arquivos reais**: upload, leitura e decodificação da imagem, capa, miniaturas, prévia na edição, galeria pública, normalização de URL antiga e estado de arquivo indisponível.
- Mantidos os testes de botão fixo, contatos, cadastro/publicação, fotos cumulativas, preservação de dados após erro, rascunho e renovação de sessão.
- Revisão visual das capturas de computador e celular.

## Implantação

As alterações precisam chegar aos contêineres da VPS; publicar o código na Main não atualiza esses processos automaticamente. Na pasta do projeto:

```bash
git pull origin main
docker compose --env-file back-end/.env.production -f docker-compose.production.yml up --build -d
```

O volume de mídia existente é mantido. Esta mudança não adiciona migração de banco e funciona com o proxy `/media/` já versionado; é necessário reconstruir também o backend, que contém a correção da rota.

Para verificar se algum cadastro aponta para um arquivo que não existe no volume:

```bash
docker compose --env-file back-end/.env.production -f docker-compose.production.yml exec api python manage.py verificar_imagens
```

O comando apenas diagnostica, sem apagar ou modificar dados. `--json` retorna o resultado estruturado.

## Limites da verificação

O acesso automatizado ao domínio em produção retornou HTTP 403; não houve acesso SSH nem deploy na VPS. A causa da configuração foi confirmada no código e reproduzida/coberta com servidor de produção local. Não se afirma que a instalação da VPS já está corrigida.

Arquivos que tenham sido removidos do volume não podem ser reconstruídos a partir do cadastro: precisam de restauração de backup ou novo envio. O painel sinaliza imagem indisponível, e o comando de diagnóstico identifica esses registros. WebKit móvel simula tela e toque; não substitui a conferência da galeria nativa em um iPhone físico.

Para repetir os testes:

```bash
python -m pip install -r back-end/requirements.txt
python back-end/manage.py test apps --settings=config.test_settings
cd front-end
npm ci
npx playwright install --with-deps chromium webkit
npm run test:e2e
```

O executor usa banco, mídia e conta descartáveis e não cria anúncios em produção.
