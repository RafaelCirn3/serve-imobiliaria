# Tarefas — captação de imóveis e busca por localização

## Objetivo

Adicionar ao projeto SERVE um botão flutuante **“Quer vender seu imóvel? Descreva aqui!”**, com formulário em modal e envio para **Servenegociosimobiliarios@gmail.com**. Preparar a busca dinâmica por cidade, bairro e rua nas cidades de **João Pessoa, Cabedelo e Bananeiras (PB)**, integrando o ViaCEP ao preenchimento de endereços e um mapa à consulta dos imóveis. Deslocar o título do hero um pouco para a esquerda, sobre o mar, preservando a visão da cidade.

As caixas marcadas indicam implementação concluída, com as verificações realizadas descritas em cada seção. As tarefas 1, 2, 4, 6 e 7 estão implementadas; a tarefa 3 aguarda entrega real via Gmail, a tarefa 5 aguarda revisão do catálogo antigo e a tarefa 8 mantém as pendências externas de entrega. Revisão dos arquivos alterados realizada em 28/09/2026.

## Decisões confirmadas

- “Enquete” refere-se ao modal de captação de imóveis da tarefa 2; não haverá uma enquete separada.
- Biblioteca de mapas: **Leaflet**, consolidada para mapas interativos e compatível com Angular. Referências: [site oficial](https://leafletjs.com/) e [guia de integração](https://leafletjs.com/examples/quick-start/). Integração implementada com MarkerCluster, tiles OpenStreetMap e geocodificação Nominatim, configuráveis pelo back-end.

## Base identificada antes da implementação

- Front-end Angular 20, com componentes standalone, Reactive Forms e serviços HTTP.
- Back-end Django REST Framework, com aplicações `properties`, `locations` e `leads`.
- `Property` já possui `cidade`, `bairro`, `endereco`, `cep`, `latitude` e `longitude`.
- A API já filtra cidade, bairro, tipo, valor, quartos e área privativa. Os filtros públicos de cidade e bairro ainda são campos de texto; a listagem já utiliza parâmetros na URL.
- `Region` relaciona nome e cidade; avaliar seu uso como cadastro de bairros sem confundir regiões comerciais com bairros oficiais.
- A captação atual registra leads. Não há configuração de envio de e-mail em `back-end/config/settings.py`.
- O hero utiliza `front-end/src/assets/hero-joao-pessoa.jpg`; seu posicionamento está em `home.component.ts`, na regra `.hero-content`.

## 1. Tipos de imóveis e perfil desejado

- [x] Padronizar os nomes exibidos: Apartamento, Área/Terreno, Casa, Condomínio fechado e Flat. Manter os tipos existentes compatíveis e adicionar `flat` ao modelo, serializers, tipos TypeScript, formulários e filtros, com migração quando necessária.
- [x] Usar “Área/Terreno” para o tipo de imóvel e “Área em m²” para metragem, evitando ambiguidade. Definir a nomenclatura pública de `condominio` como “Condomínio fechado”.
- [x] Oferecer busca pelo perfil desejado: tipo, quantidade mínima de quartos, faixa de área, cidade, bairro e faixa de valor. Explicitar se a metragem é privativa ou total; para terrenos, contemplar área total.
- [x] Atualizar textos hoje restritos a João Pessoa para refletir as três cidades atendidas, inclusive o título da listagem e as opções da busca do hero.
- [x] Exibir a quantidade real de imóveis publicados. Usar o contexto comercial de realização do sonho e investimento sem afirmar “milhares de imóveis” antes de confirmar o estoque.

**Implementado:** opções compartilhadas em `core/models/property-options.ts`, tipo `flat` e migração `0003_property_types.py`, seletores públicos e administrativos consistentes, áreas identificadas nos cards/detalhe, filtros `area_total_min`/`area_total_max`, validação de faixas na API e no formulário, restauração dos campos ao mudar os parâmetros da URL, textos e contador real na home.

**Verificação:** build de produção do Angular aprovado; 8 testes de integração da API aprovados em SQLite isolado, incluindo cadastro/publicação de Flat, tipos antigos, filtros combinados, área total de terrenos, valores inválidos e exclusão de rascunhos do contador público. Django `check` aprovado e `makemigrations --check --dry-run` sem alterações pendentes.

**Navegador:** home e listagem verificadas com `agent-browser`, usando API real e banco SQLite exclusivo de verificação. O fluxo home → Flat/Cabedelo → filtros de preço, quartos e área retornou um resultado correto. A URL de Bananeiras com `area_total_min=350&area_total_max=450` restaurou os filtros e exibiu o terreno de 400 m². Máximo abaixo do mínimo desabilitou o envio. Layouts desktop e celular (390px) sem rolagem horizontal; nenhum erro de execução reportado pelo navegador. Dados e capturas de verificação ficam em `.venv/`, fora do versionamento.

**Implantação:** executar `python manage.py migrate` no ambiente com PostgreSQL configurado. As credenciais padrão locais foram recusadas; nenhuma alteração foi aplicada ao PostgreSQL existente. A migração foi exercitada no banco isolado de testes.

**Aceite:** os tipos estão consistentes entre administração, API e busca pública; filtros combinados retornam os imóveis correspondentes e a metragem utilizada está identificada.

## 2. Botão flutuante e modal de venda

**Progresso:** Modal e CTA global implementados e verificados por teclado e no celular. Foco inicial, Tab, Escape, retorno do foco, bloqueio de rolagem, validação, envio e ocultação nas rotas administrativas aprovados. Na revisão, o botão passou a observar mudanças de conteúdo/layout e usar signals para atualizar a visibilidade. Rolagem em 1440px e 390px validou ausência de sobreposição com controles e atribuição do mapa; o botão fica temporariamente oculto quando necessário.

- [x] Criar componente compartilhado para o botão com o texto exato **“Quer vender seu imóvel? Descreva aqui!”** e incluí-lo nas páginas públicas, ocultando-o nas rotas administrativas.
- [x] Posicionar o botão fixo com espaçamento responsivo, respeitando áreas seguras do celular e evitando sobreposição com controles, rodapé e outros botões flutuantes.
- [x] Ao clicar, abrir um modal com nome, e-mail, telefone/WhatsApp e descrição obrigatórios. Incluir tipo de imóvel, CEP, cidade, bairro, rua, número/complemento, quartos, área em m² e valor pretendido como informações adicionais.
- [x] Usar Reactive Forms, rótulos visíveis, validações e mensagens junto aos campos. Informar que os dados serão usados pela SERVE para retornar o contato.
- [x] Implementar acessibilidade: identificação do diálogo, foco inicial, foco contido no modal, fechamento por Escape e botão de fechar, retorno do foco ao botão e bloqueio da rolagem de fundo.
- [x] Exibir estados de envio, sucesso e falha; bloquear envios repetidos enquanto a requisição estiver em andamento e preservar os dados se houver erro.
- [x] Fazer o CTA existente para proprietários na home abrir o mesmo modal.

**Arquivos envolvidos:** `front-end/src/app/shared/components/`, páginas em `features/public/`, `core/services/lead.service.ts` e `core/models/api.models.ts`.

**Aceite:** o botão abre o modal nas páginas públicas, funciona por teclado e no celular, e o formulário envia os dados sem depender de um aplicativo de e-mail instalado.

## 3. Captação e envio real de e-mail

**Progresso:** Captação, idempotência, persistência antes da notificação, destinatário fixo, limite por IP, painel e comando de reenvio implementados. Gmail SMTP com senha de aplicativo escolhido pelo usuário. Testes usam e-mail em memória: não foi realizada entrega externa. A revisão reforçou o telefone para exigir 10–15 dígitos e aplicou o limite de ofertas também a usuários autenticados.

- [x] Estender `apps/leads` para identificar a origem `venda_imovel` e armazenar os dados do imóvel oferecido, sem exigir vínculo com um imóvel já cadastrado. Atualizar administração e contratos TypeScript.
- [x] Criar endpoint público específico, por exemplo `POST /api/leads/venda-imovel/`, com validação no servidor e destinatário fixo configurado pelo back-end.
- [x] Persistir o lead e registrar o estado da notificação. Prever reenvio de notificações com falha e prevenção de duplicidade nas tentativas do mesmo envio.
- [x] Configurar o serviço de e-mail no Django com credenciais em variáveis de ambiente e documentar a configuração no exemplo de ambiente e README. Utilizar remetente autorizado pelo provedor e `Reply-To` com o e-mail informado pelo proprietário.
- [ ] Validar a entrega real da notificação para **Servenegociosimobiliarios@gmail.com**, com assunto identificando a oferta e corpo contendo contato, descrição, localização e características preenchidas. Não interpolar entradas do usuário em cabeçalhos sem validação.
- [x] Separar “solicitação registrada” de “e-mail enviado”: informar corretamente o resultado e manter a solicitação disponível para atendimento mesmo se a notificação falhar.
- [x] Aplicar limites de tamanho, frequência e proteção básica contra spam no endpoint público; não expor credenciais ou dados pessoais nos logs.

**Arquivos envolvidos:** `back-end/apps/leads/{models,serializers,views,admin}.py`, migrações, `back-end/config/{settings,urls}.py` e serviço Angular de leads.

**Aceite:** uma submissão válida gera um lead de venda e uma notificação ao destinatário; falha no provedor não perde os dados nem produz mensagem falsa de envio bem-sucedido. A entrega deve ser verificada em ambiente configurado.

## 4. Endereço dinâmico com ViaCEP

**Progresso:** ViaCEP centralizado com cache, timeout e editor compartilhado. CEPs reais de João Pessoa e São Paulo, preenchimento manual e preservação de número/complemento verificados. Na revisão, consultas antigas passaram a ser canceladas imediatamente ao editar, mantendo o debounce dentro da consulta. Testes no navegador com respostas atrasadas validaram CEP mais recente, edição manual, erro antigo e descarte de sugestões após selecionar um endereço.

Referência técnica: [documentação oficial do ViaCEP](https://viacep.com.br/).

O ViaCEP consulta CEPs e pesquisa endereços; não fornece coordenadas nem um catálogo completo de bairros de uma cidade. A pesquisa por endereço exige UF, cidade e logradouro, com ao menos três caracteres nos dois últimos, e retorna até 50 CEPs. Os filtros do catálogo devem consultar a base da SERVE.

- [x] Criar serviço reutilizável de consulta por CEP e pesquisa por rua, preferencialmente com integração centralizada no back-end e contrato consumido pelo Angular.
- [x] Normalizar e validar oito dígitos antes de consultar `https://viacep.com.br/ws/{cep}/json/`; tratar `erro: true`, HTTP 400, indisponibilidade e timeout.
- [x] Preencher cidade, UF, bairro e logradouro no cadastro administrativo e no modal de venda. Manter edição manual para dados ausentes ou desatualizados e preservar número e complemento do usuário.
- [x] Implementar sugestões por `https://viacep.com.br/ws/PB/{cidade}/{logradouro}/json/`, codificando os segmentos da URL e consultando somente após os critérios mínimos.
- [x] Aplicar debounce, cancelamento de consultas antigas, cache e limites de requisições. Não fazer varredura massiva de CEPs para construir uma base de bairros.
- [x] Validar as cidades atendidas e UF PB no cadastro do catálogo. No modal, informar claramente quando um endereço estiver fora da área de atendimento, sem substituir silenciosamente a localização.

**Aceite:** CEP válido preenche os dados disponíveis; CEP inválido, inexistente ou serviço indisponível apresenta orientação clara e permite preenchimento manual. Respostas antigas não sobrescrevem o endereço atual.

## 5. Filtros dependentes: cidade → bairro → rua

**Progresso:** Endereços estruturados e normalizados, migrações, opções provenientes apenas de imóveis publicados, filtros dependentes e restauração pela URL implementados. Testes da API cobrem as três cidades e o navegador confirmou limpeza de dependências e isolamento dos bairros. Na revisão, a busca textual do front-end passou a utilizar o mesmo endpoint e parâmetro search na lista e no mapa, incluindo buscas com várias palavras. O endereço antigo é preservado sem inferir ruas; a revisão manual do catálogo real continua pendente.

- [x] Disponibilizar seleção de João Pessoa, Cabedelo e Bananeiras, com opção inicial “Todas as cidades”.
- [x] Criar endpoints em `apps/locations` para bairros por cidade e ruas por cidade/bairro, usando endereços dos imóveis publicados como fonte das opções públicas. Aproveitar `Region` quando representar efetivamente um bairro.
- [x] Separar logradouro, número, complemento e UF e criar migração compatível, preservando o endereço antigo sem classificação automática de ruas.
- [ ] Revisar manualmente os endereços do catálogo real e preencher ruas/números/complementos estruturados.
- [x] Normalizar espaços, grafias e comparação de acentos/maiúsculas para evitar opções duplicadas, preservando nomes legíveis na apresentação.
- [x] Substituir os campos livres de localização por seletores/autocomplete dependentes em `filter-sidebar.component.ts` e `search-bar.component.ts`.
- [x] Ao mudar a cidade, limpar bairro e rua; ao mudar o bairro, limpar rua. Desabilitar seleções dependentes até que a localização anterior esteja definida.
- [x] Adicionar filtros de logradouro e CEP ao back-end e a `PropertyFilters`; combinar com os filtros comerciais existentes.
- [x] Sincronizar filtros com a URL, restaurar estado ao recarregar/voltar e reiniciar a paginação ao alterar critérios. Cancelar requisições anteriores para evitar resultados desatualizados.
- [x] Implementar carregamento, erros de API, contador de resultados, limpeza de filtros e mensagem de ausência de imóveis; diferenciar erro de carregamento de catálogo vazio.

**Arquivos envolvidos:** `apps/locations/`, `apps/properties/{models,filters,views,serializers}.py`, serviços de região e imóveis, modelos TypeScript e `features/public/properties/properties.component.ts`.

**Aceite:** selecionar Cabedelo mostra apenas seus bairros; selecionar um bairro restringe suas ruas; resultados combinam todos os critérios e nenhum imóvel não publicado aparece nas opções ou na listagem.

## 6. Visualização dos imóveis nas ruas

**Progresso:** Leaflet e MarkerCluster integrados à listagem, detalhe e prévia administrativa; endpoint dedicado cobre múltiplas páginas e informa limite/truncamento e imóveis sem coordenadas. Tiles OpenStreetMap e Nominatim documentados e configuráveis. Coordenadas públicas aproximadas por padrão. Na revisão, avisos de falha de tiles passaram a usar signals e sugestões de geocodificação são descartadas se endereço/coordenadas forem alterados durante a consulta. A API valida geocodificação simulada, cache, limites, autorização e coordenadas; cobertura/entrega do geocodificador real no ambiente de implantação ainda requer validação.

Interpretação de escopo: mapa interativo com ruas e marcadores dos imóveis, sincronizado com a lista. Uma experiência de Street View não está incluída nesta etapa.

- [x] Selecionar a biblioteca de mapas: Leaflet, conforme decisão registrada acima.
- [x] Selecionar provedor de tiles e geocodificação com cobertura nas três cidades; registrar limites, atribuição, custos e configuração necessária antes de integrar.
- [x] Reutilizar `latitude` e `longitude` existentes. Para imóveis sem coordenadas, geocodificar endereços completos durante o cadastro/edição, armazenar o resultado e permitir ajuste manual pelo administrador. Evitar geocodificar a cada visita pública.
- [x] Validar coordenadas e distinguir posição confirmada de localização aproximada; endereços sem número ou com CEP geral não devem gerar falsa precisão.
- [x] Criar modo “Lista / Mapa”, marcadores com título, foto, preço e link para o detalhe; agrupar marcadores quando houver concentração e ajustar o enquadramento aos resultados.
- [x] Criar consulta de marcadores com os mesmos filtros da lista, cobrindo todos os resultados dentro de limites explícitos ou da área visível. Não limitar silenciosamente o mapa à primeira página da listagem.
- [x] Sincronizar alterações de cidade, bairro e rua com lista e mapa. Mostrar imóveis sem coordenadas na lista e informar quando não puderem ser exibidos no mapa.
- [x] Incluir mapa no detalhe do imóvel, substituindo a apresentação atual apenas numérica das coordenadas, e definir se a localização pública será exata ou aproximada por imóvel.
- [x] Garantir navegação acessível pela lista e funcionamento dos filtros se o mapa estiver indisponível.

**Aceite:** ao selecionar cidade, bairro e rua, lista e mapa representam o mesmo recorte; marcadores abrem o detalhe correto e imóveis sem coordenadas continuam acessíveis na lista.

## 7. Título do hero mais à esquerda, sobre o mar

**Progresso:** Imagem original inspecionada e preservada. Título deslocado de 7vw para 3,5vw (máximo 60px), largura de 540px, gradiente localizado e margem de 16px no celular. Capturas em 1440, 1024, 768 e 390px confirmaram leitura e ausência de rolagem horizontal. Ajuste do botão flutuante foi verificado também na página do mapa em desktop e celular.

- [x] Inspecionar `front-end/src/assets/hero-joao-pessoa.jpg` e a composição atual em desktop, tablet e celular.
- [x] Reduzir o deslocamento horizontal de `.hero-content` em `front-end/src/app/features/public/home/home.component.ts`, atualmente `margin-left: clamp(0px, 7vw, 120px)`, posicionando o título um pouco mais à esquerda sobre o mar.
- [x] Ajustar largura do texto e, se necessário, `background-position` e gradiente para preservar leitura e visão ampla da cidade, mantendo a imagem original.
- [x] Preservar espaçamento lateral no celular e garantir que título, subtítulo, busca e novo botão flutuante não se sobreponham.
- [x] Comparar capturas antes/depois em 1440px, 1024px, 768px e 390px.

**Aceite:** no desktop, o título fica mais à esquerda sobre o mar e libera a vista da cidade; em telas menores, o conteúdo permanece legível, sem cortes nem rolagem horizontal.

## 8. Verificação e entrega

- [x] Verificar o fluxo completo de venda com e-mail em memória: abertura do modal → validação → API → lead registrado → notificação simulada → confirmação ao usuário.
- [ ] Repetir o fluxo com Gmail SMTP configurado e conferir a entrega real na caixa destinatária.
- [x] Cobrir com testes do back-end as validações, envio simulado de e-mail, falha do provedor, repetição do envio, filtros dependentes e exclusão de imóveis não publicados. Usar respostas simuladas do ViaCEP nos testes automatizados.
- [x] Verificar ViaCEP com endereço válido, inválido, inexistente e sem bairro/logradouro, além de timeout e respostas fora de ordem.
- [ ] Verificar filtros e mapa nas três cidades, incluindo ausência de resultados, imóveis sem coordenadas, múltiplas páginas e restauração dos filtros pela URL.
- [x] Executar `npm run build` em `front-end` e `python manage.py check`, `python manage.py makemigrations --check --dry-run` e os testes relevantes em `back-end`, com o ambiente configurado.
- [x] Documentar variáveis de ambiente, migrações, escolha do provedor de mapa, configuração de e-mail e procedimento de reenvio de notificações.

## Ordem sugerida e decisões

As implementações foram realizadas seguindo a numeração. As pendências abaixo exigem configuração do ambiente e dados reais; não impedem a revisão local com banco isolado e e-mail simulado.

- [x] Definir o provedor de e-mail: Gmail via SMTP com senha de aplicativo.
- [ ] Configurar credenciais exclusivamente no `back-end/.env` e conferir a entrega na caixa destinatária.
- [x] Definir OpenStreetMap/Nominatim, configurações e política de localização pública aproximada por padrão.
- [x] Confirmar o significado de “Enquete”: o usuário esclareceu que se trata do modal da tarefa 2. Não criar questionário separado.

## Registro da revisão — 28/09/2026

**Correções realizadas:**

- Cancelamento imediato de consultas antigas de CEP/rua e proteção contra mensagens/sugestões atrasadas, preservando edições manuais.
- Descarte da sugestão de geocodificação quando o endereço ou as coordenadas mudam durante a consulta; bloqueio de consultas simultâneas no cadastro e cancelamento ao sair da página.
- Critérios de busca textual iguais na lista e no mapa, inclusive buscas com várias palavras.
- Validação de telefone com quantidade real de dígitos e limites por IP também para usuários autenticados.
- Atualização reativa da posição/visibilidade do CTA após mudanças de conteúdo e layout e dos avisos de indisponibilidade de tiles.
- Novos testes de regressão para telefone, limites autenticados e paridade entre busca da lista e do mapa; READMEs atualizados.

**Verificações desta revisão:**

- 39 testes de API aprovados com SQLite isolado, ViaCEP/geocodificação simulados e e-mail em memória.
- 21 verificações do fluxo integrado no navegador aprovadas: quatro tamanhos de tela, modal/teclado, CEPs reais, falha de consulta, registro de oferta, filtros por URL, bairros dependentes, agrupamento de marcadores, popup/detalhe e ocultação do CTA no administrativo.
- `npm run build` aprovado; Django `check` aprovado; `makemigrations --check --dry-run --settings=config.test_settings` sem mudanças pendentes; `git diff --check` sem erros de whitespace.
- 12 verificações adicionais no navegador aprovadas: cinco casos de respostas atrasadas/edições de endereço, CTA e ausência de overflow em 1440px/390px, busca textual equivalente em lista/mapa e ausência de erros de execução. Total: 33 verificações aprovadas. Capturas e scripts locais ficam em `back-end/.venv/`, fora do versionamento.

**Pendências para concluir a entrega:**

- Configurar Gmail SMTP com senha de aplicativo no `.env` e conferir uma entrega real para **Servenegociosimobiliarios@gmail.com**.
- Configurar o PostgreSQL de destino e aplicar as migrações; o PostgreSQL existente não foi alterado durante a revisão. Usar cache compartilhado em produção conforme o README.
- Revisar endereços antigos do catálogo real antes de depender da seleção de ruas.
- Validar o fluxo administrativo completo de localizar/ajustar/salvar com o provedor real e repetir os cenários finais do mapa (sem coordenadas, vazio e múltiplas páginas) no ambiente de entrega. Esses cenários já têm cobertura na API, com serviços simulados quando necessário.
