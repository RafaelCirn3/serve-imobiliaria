# Tarefas — captação de imóveis e busca por localização

## Objetivo

Adicionar ao projeto SERVE um botão flutuante **“Quer vender seu imóvel? Descreva aqui!”**, com formulário em modal e envio para **Servenegociosimobiliarios@gmail.com**. Preparar a busca dinâmica por cidade, bairro e rua nas cidades de **João Pessoa, Cabedelo e Bananeiras (PB)**, integrando o ViaCEP ao preenchimento de endereços e um mapa à consulta dos imóveis. Deslocar o título do hero um pouco para a esquerda, sobre o mar, preservando a visão da cidade.

As caixas marcadas indicam itens implementados e verificados. A tarefa 1 foi concluída; as demais permanecem pendentes, salvo as decisões registradas abaixo.

## Decisões confirmadas

- “Enquete” refere-se ao modal de captação de imóveis da tarefa 2; não haverá uma enquete separada.
- Biblioteca de mapas: **Leaflet**, consolidada para mapas interativos e compatível com Angular. Referências: [site oficial](https://leafletjs.com/) e [guia de integração](https://leafletjs.com/examples/quick-start/). A integração ocorrerá na tarefa 6; tiles e geocodificação continuam sujeitos à escolha de provedor.

## Base existente

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

- [ ] Criar componente compartilhado para o botão com o texto exato **“Quer vender seu imóvel? Descreva aqui!”** e incluí-lo nas páginas públicas, ocultando-o nas rotas administrativas.
- [ ] Posicionar o botão fixo com espaçamento responsivo, respeitando áreas seguras do celular e evitando sobreposição com controles, rodapé e outros botões flutuantes.
- [ ] Ao clicar, abrir um modal com nome, e-mail, telefone/WhatsApp e descrição obrigatórios. Incluir tipo de imóvel, CEP, cidade, bairro, rua, número/complemento, quartos, área em m² e valor pretendido como informações adicionais.
- [ ] Usar Reactive Forms, rótulos visíveis, validações e mensagens junto aos campos. Informar que os dados serão usados pela SERVE para retornar o contato.
- [ ] Implementar acessibilidade: identificação do diálogo, foco inicial, foco contido no modal, fechamento por Escape e botão de fechar, retorno do foco ao botão e bloqueio da rolagem de fundo.
- [ ] Exibir estados de envio, sucesso e falha; bloquear envios repetidos enquanto a requisição estiver em andamento e preservar os dados se houver erro.
- [ ] Fazer o CTA existente para proprietários na home abrir o mesmo modal.

**Arquivos envolvidos:** `front-end/src/app/shared/components/`, páginas em `features/public/`, `core/services/lead.service.ts` e `core/models/api.models.ts`.

**Aceite:** o botão abre o modal nas páginas públicas, funciona por teclado e no celular, e o formulário envia os dados sem depender de um aplicativo de e-mail instalado.

## 3. Captação e envio real de e-mail

- [ ] Estender `apps/leads` para identificar a origem `venda_imovel` e armazenar os dados do imóvel oferecido, sem exigir vínculo com um imóvel já cadastrado. Atualizar administração e contratos TypeScript.
- [ ] Criar endpoint público específico, por exemplo `POST /api/leads/venda-imovel/`, com validação no servidor e destinatário fixo configurado pelo back-end.
- [ ] Persistir o lead e registrar o estado da notificação. Prever reenvio de notificações com falha e prevenção de duplicidade nas tentativas do mesmo envio.
- [ ] Configurar o serviço de e-mail no Django com credenciais em variáveis de ambiente e documentar a configuração no exemplo de ambiente e README. Utilizar remetente autorizado pelo provedor e `Reply-To` com o e-mail informado pelo proprietário.
- [ ] Enviar a notificação para **Servenegociosimobiliarios@gmail.com**, com assunto identificando a oferta e corpo contendo contato, descrição, localização e características preenchidas. Não interpolar entradas do usuário em cabeçalhos sem validação.
- [ ] Separar “solicitação registrada” de “e-mail enviado”: informar corretamente o resultado e manter a solicitação disponível para atendimento mesmo se a notificação falhar.
- [ ] Aplicar limites de tamanho, frequência e proteção básica contra spam no endpoint público; não expor credenciais ou dados pessoais nos logs.

**Arquivos envolvidos:** `back-end/apps/leads/{models,serializers,views,admin}.py`, migrações, `back-end/config/{settings,urls}.py` e serviço Angular de leads.

**Aceite:** uma submissão válida gera um lead de venda e uma notificação ao destinatário; falha no provedor não perde os dados nem produz mensagem falsa de envio bem-sucedido. A entrega deve ser verificada em ambiente configurado.

## 4. Endereço dinâmico com ViaCEP

Referência técnica: [documentação oficial do ViaCEP](https://viacep.com.br/).

O ViaCEP consulta CEPs e pesquisa endereços; não fornece coordenadas nem um catálogo completo de bairros de uma cidade. A pesquisa por endereço exige UF, cidade e logradouro, com ao menos três caracteres nos dois últimos, e retorna até 50 CEPs. Os filtros do catálogo devem consultar a base da SERVE.

- [ ] Criar serviço reutilizável de consulta por CEP e pesquisa por rua, preferencialmente com integração centralizada no back-end e contrato consumido pelo Angular.
- [ ] Normalizar e validar oito dígitos antes de consultar `https://viacep.com.br/ws/{cep}/json/`; tratar `erro: true`, HTTP 400, indisponibilidade e timeout.
- [ ] Preencher cidade, UF, bairro e logradouro no cadastro administrativo e no modal de venda. Manter edição manual para dados ausentes ou desatualizados e preservar número e complemento do usuário.
- [ ] Implementar sugestões por `https://viacep.com.br/ws/PB/{cidade}/{logradouro}/json/`, codificando os segmentos da URL e consultando somente após os critérios mínimos.
- [ ] Aplicar debounce, cancelamento de consultas antigas, cache e limites de requisições. Não fazer varredura massiva de CEPs para construir uma base de bairros.
- [ ] Validar as cidades atendidas e UF PB no cadastro do catálogo. No modal, informar claramente quando um endereço estiver fora da área de atendimento, sem substituir silenciosamente a localização.

**Aceite:** CEP válido preenche os dados disponíveis; CEP inválido, inexistente ou serviço indisponível apresenta orientação clara e permite preenchimento manual. Respostas antigas não sobrescrevem o endereço atual.

## 5. Filtros dependentes: cidade → bairro → rua

- [ ] Disponibilizar seleção de João Pessoa, Cabedelo e Bananeiras, com opção inicial “Todas as cidades”.
- [ ] Criar endpoints em `apps/locations` para bairros por cidade e ruas por cidade/bairro, usando endereços dos imóveis publicados como fonte das opções públicas. Aproveitar `Region` quando representar efetivamente um bairro.
- [ ] Separar logradouro, número, complemento e UF no modelo de endereço quando necessário. Criar migração compatível e revisar os endereços antigos antes de classificá-los automaticamente por rua.
- [ ] Normalizar espaços, grafias e comparação de acentos/maiúsculas para evitar opções duplicadas, preservando nomes legíveis na apresentação.
- [ ] Substituir os campos livres de localização por seletores/autocomplete dependentes em `filter-sidebar.component.ts` e `search-bar.component.ts`.
- [ ] Ao mudar a cidade, limpar bairro e rua; ao mudar o bairro, limpar rua. Desabilitar seleções dependentes até que a localização anterior esteja definida.
- [ ] Adicionar filtros de logradouro e CEP ao back-end e a `PropertyFilters`; combinar com os filtros comerciais existentes.
- [ ] Sincronizar filtros com a URL, restaurar estado ao recarregar/voltar e reiniciar a paginação ao alterar critérios. Cancelar requisições anteriores para evitar resultados desatualizados.
- [ ] Implementar carregamento, erros de API, contador de resultados, limpeza de filtros e mensagem de ausência de imóveis; diferenciar erro de carregamento de catálogo vazio.

**Arquivos envolvidos:** `apps/locations/`, `apps/properties/{models,filters,views,serializers}.py`, serviços de região e imóveis, modelos TypeScript e `features/public/properties/properties.component.ts`.

**Aceite:** selecionar Cabedelo mostra apenas seus bairros; selecionar um bairro restringe suas ruas; resultados combinam todos os critérios e nenhum imóvel não publicado aparece nas opções ou na listagem.

## 6. Visualização dos imóveis nas ruas

Interpretação de escopo: mapa interativo com ruas e marcadores dos imóveis, sincronizado com a lista. Uma experiência de Street View não está incluída nesta etapa.

- [x] Selecionar a biblioteca de mapas: Leaflet, conforme decisão registrada acima.
- [ ] Selecionar provedor de tiles e geocodificação com cobertura nas três cidades; registrar limites, atribuição, custos e configuração necessária antes de integrar.
- [ ] Reutilizar `latitude` e `longitude` existentes. Para imóveis sem coordenadas, geocodificar endereços completos durante o cadastro/edição, armazenar o resultado e permitir ajuste manual pelo administrador. Evitar geocodificar a cada visita pública.
- [ ] Validar coordenadas e distinguir posição confirmada de localização aproximada; endereços sem número ou com CEP geral não devem gerar falsa precisão.
- [ ] Criar modo “Lista / Mapa”, marcadores com título, foto, preço e link para o detalhe; agrupar marcadores quando houver concentração e ajustar o enquadramento aos resultados.
- [ ] Criar consulta de marcadores com os mesmos filtros da lista, cobrindo todos os resultados dentro de limites explícitos ou da área visível. Não limitar silenciosamente o mapa à primeira página da listagem.
- [ ] Sincronizar alterações de cidade, bairro e rua com lista e mapa. Mostrar imóveis sem coordenadas na lista e informar quando não puderem ser exibidos no mapa.
- [ ] Incluir mapa no detalhe do imóvel, substituindo a apresentação atual apenas numérica das coordenadas, e definir se a localização pública será exata ou aproximada por imóvel.
- [ ] Garantir navegação acessível pela lista e funcionamento dos filtros se o mapa estiver indisponível.

**Aceite:** ao selecionar cidade, bairro e rua, lista e mapa representam o mesmo recorte; marcadores abrem o detalhe correto e imóveis sem coordenadas continuam acessíveis na lista.

## 7. Título do hero mais à esquerda, sobre o mar

- [ ] Inspecionar `front-end/src/assets/hero-joao-pessoa.jpg` e a composição atual em desktop, tablet e celular.
- [ ] Reduzir o deslocamento horizontal de `.hero-content` em `front-end/src/app/features/public/home/home.component.ts`, atualmente `margin-left: clamp(0px, 7vw, 120px)`, posicionando o título um pouco mais à esquerda sobre o mar.
- [ ] Ajustar largura do texto e, se necessário, `background-position` e gradiente para preservar leitura e visão ampla da cidade, mantendo a imagem original.
- [ ] Preservar espaçamento lateral no celular e garantir que título, subtítulo, busca e novo botão flutuante não se sobreponham.
- [ ] Comparar capturas antes/depois em 1440px, 1024px, 768px e 390px.

**Aceite:** no desktop, o título fica mais à esquerda sobre o mar e libera a vista da cidade; em telas menores, o conteúdo permanece legível, sem cortes nem rolagem horizontal.

## 8. Verificação e entrega

- [ ] Verificar o fluxo completo de venda: abertura do modal → validação → API → lead registrado → notificação → confirmação ao usuário.
- [ ] Cobrir com testes do back-end as validações, envio simulado de e-mail, falha do provedor, repetição do envio, filtros dependentes e exclusão de imóveis não publicados. Usar respostas simuladas do ViaCEP nos testes automatizados.
- [ ] Verificar ViaCEP com endereço válido, inválido, inexistente e sem bairro/logradouro, além de timeout e respostas fora de ordem.
- [ ] Verificar filtros e mapa nas três cidades, incluindo ausência de resultados, imóveis sem coordenadas, múltiplas páginas e restauração dos filtros pela URL.
- [ ] Executar `npm run build` em `front-end` e `python manage.py check`, `python manage.py makemigrations --check --dry-run` e os testes relevantes em `back-end`, com o ambiente configurado.
- [ ] Documentar variáveis de ambiente, migrações, escolha do provedor de mapa, configuração de e-mail e procedimento de reenvio de notificações.

## Ordem sugerida e decisões

Executar o ajuste do hero independentemente. Para a captação, implementar contrato e envio de e-mail antes de conectar o modal. Para localização, estruturar endereço e ViaCEP, depois filtros dependentes e mapa, finalizando com verificação integrada.

- [ ] Definir o provedor de e-mail e configurar suas credenciais para validar a entrega real.
- [ ] Definir provedores de mapa/geocodificação e política de exposição do endereço.
- [x] Confirmar o significado de “Enquete”: o usuário esclareceu que se trata do modal da tarefa 2. Não criar questionário separado.
