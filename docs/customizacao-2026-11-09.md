# Vistoria e implementação da customização — SERVE

Data: 09/11/2026. Entrega no código da branch `main`.

## Resultado da vistoria

O painel anterior não oferecia a experiência de edição solicitada. As configurações estavam distribuídas entre Vitrines de imóveis, Fotos da página inicial, Textos da página inicial, Carrossel principal e Regiões. A edição se concentrava na home; outras páginas e informações compartilhadas mantinham textos no código. Também faltava uma prévia integrada do resultado antes da publicação.

Esses pontos foram tratados com uma área única, em `/admin/customizacao`, conectada às próprias páginas públicas. Imóveis e contatos continuam em seus módulos específicos.

## Proposta implementada

O menu agora reúne Visão geral, Imóveis, Contatos recebidos e **Customização**. Dentro de Customização há um pequeno menu de páginas: Início, Imóveis, Sobre nós, Contato, Página do imóvel e Geral / rodapé.

Cada aba apresenta primeiro a prévia real do site e, abaixo, os campos de edição. A prévia usa os componentes públicos, com o rascunho aplicado somente dentro do quadro. Alterar um campo atualiza a ilustração sem publicar. Há opções de visualização de computador e celular.

Os indicadores distinguem versão publicada, alterações não salvas, preparação de imagens e salvamento. O botão **Salvar alterações** publica o rascunho completo, incluindo mudanças feitas em outras abas. **Descartar alterações** recupera a última versão carregada ou salva. A troca entre abas mantém o preenchimento.

## Áreas editáveis

| Área | Conteúdo disponível no editor |
| --- | --- |
| Início | Textos de abertura e seções, chamada da busca, títulos, botões, carrossel principal, fotos informativas, vitrines e regiões |
| Imóveis | Identificação e título do catálogo, cidades padrão e rótulos das visualizações |
| Sobre nós | Imagem de abertura, títulos, apresentação e quatro diferenciais |
| Contato | Títulos, apresentação, chamada para proprietários, placeholders e botão do formulário |
| Página do imóvel | Textos dos botões de retorno e interesse e título de imóveis semelhantes |
| Geral / rodapé | Nome, assinatura e logotipo da marca, CRECI, navegação, WhatsApp, e-mail, endereço, Instagram, textos e títulos do rodapé e chamada flutuante |
| Blocos existentes | Mostrar ou ocultar, ordem, espaçamento, alinhamento e fundo claro, escuro ou original |

Cabeçalho e rodapé mantêm sua posição estrutural. As opções de ordem atuam sobre os blocos previstos em cada página e respeitam os agrupamentos de formulários e informações do imóvel.

Os dados individuais dos imóveis, suas fotografias e publicação continuam sendo administrados em **Imóveis**. A prévia da página de detalhes utiliza um imóvel publicado; sem um, o editor informa essa condição e ainda permite configurar os textos.

## Correções e proteções

- Eliminação dos cinco acessos separados de conteúdo no menu; endereços antigos redirecionam para Customização.
- Integração dos textos e imagens existentes ao documento de edição, sem apagar os registros anteriores.
- Carregamento centralizado do conteúdo publicado nas páginas públicas.
- Prévia imediata de textos, imagens e aparência dos blocos, sem precisar salvar para avaliar o resultado.
- Upload com miniatura e preparação de formatos, inclusive HEIC/HEIF suportados pelo backend. O arquivo preparado só passa a ser usado pelo conteúdo público após Salvar.
- Imóveis das vitrines apresentados com fotos e indicação de publicação.
- Salvamento transacional: uma validação inválida impede a publicação parcial do documento.
- Detecção de alterações concorrentes: uma versão antiga recebe aviso e mantém o rascunho, evitando sobrescrever outra publicação silenciosamente.
- Aviso ao sair com alterações pendentes e opção de descarte explícito.
- Formulários e links externos bloqueados dentro da prévia, para não gerar contatos reais durante a edição.
- Edição e upload restritos à administração; conteúdo público exclui itens inativos e imóveis não publicados das vitrines.

## Como utilizar

1. Entrar no painel e abrir **Customização**.
2. Escolher a página no menu superior.
3. Alterar os campos ou os controles dos blocos e conferir a prévia acima.
4. Alternar entre computador e celular para conferir a apresentação.
5. Clicar em **Salvar alterações** para publicar todo o rascunho, ou em **Descartar alterações** para retornar ao conteúdo salvo.

O rascunho fica na sessão aberta do editor. Ele não é um histórico de versões nem um rascunho persistido para recuperação depois de fechar o navegador.

## Escopo da liberdade de edição

A customização abrange os textos e blocos listados acima. O proprietário pode modificar conteúdo e apresentação dos blocos existentes usando controles definidos. Inserir novas páginas, criar estruturas arbitrárias de HTML/CSS, mudar regras de negócio ou editar cada mensagem de validação do sistema ainda exige desenvolvimento. Esta entrega não constitui um construtor livre de páginas.

## Validação

- **68 testes do backend aprovados**, incluindo 13 testes específicos de customização: permissões, conteúdo público, uploads, validação, publicação, atomicidade e conflito entre versões.
- Build Angular de produção aprovado.
- Verificações Django e de migrações sem pendências adicionais.
- Fluxos de navegador aprovados em **Chromium, 1440 × 900**, e **WebKit, 390 × 844**: edição e prévia, visibilidade, ordem e alinhamento de blocos, upload, seleção de vitrines, salvar, descarte e conflito com preservação do rascunho.
- Regressões anteriores aprovadas nos dois navegadores: CTA fixo, contatos, cadastro e publicação, preservação de fotos, imagens servidas com `DEBUG=False` e Gunicorn e ausência de transbordamento horizontal nas telas administrativas.

Os testes usam banco e mídia temporários, sem alterar os dados do cliente. O ensaio WebKit verifica a interface móvel; não substitui um teste em aparelho iPhone físico.

## Atualização do servidor

O código foi preparado para o deploy existente. É necessário atualizar frontend e backend juntos, pois o editor utiliza os novos endpoints e a migração `0005_customizationasset_sitecustomization`.

```bash
git pull origin main
docker compose --env-file back-end/.env.production -f docker-compose.production.yml up --build -d
```

O comando de inicialização existente do backend aplica as migrações. A publicação na Main não comprova que a VPS já executou esse deploy; a entrada do cliente e a conferência do domínio devem ocorrer após a atualização do servidor.
