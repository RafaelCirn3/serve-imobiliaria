# Relatório de correções — SERVE — 06/11/2026

Base: Main no commit `d582d3fe1aef8c6abb1c7aa00fa36b14555253c5`.

## Alterações

| Problema | Correção |
| --- | --- |
| Botão para proprietários aparecia apenas depois de rolar | Removida a lógica que ocultava o botão por colisão com outros controles. Posição fixa desde a primeira renderização, respeitando a área segura do aparelho, com `z-index: 2147483647`. O formulário modal continua na camada nativa de diálogos. |
| Texto do botão antigo | “Quer Vender ou Alugar seu Imóvel? Descreva Aqui!”. A oferta também permite escolher venda ou aluguel. |
| Administração sem navegação no iPhone | Menu administrativo expansível em telas de até 820 px, com links para as mesmas ferramentas do computador. |
| Segunda seleção apagava fotos anteriores | Seleções acumulativas, identificação de duplicatas e remoção individual antes de enviar. Cancelar o seletor mantém as fotos anteriores. |
| Fotos desapareciam ao alternar abas | Estado dos arquivos controlado pelo formulário pai; abas preservam seus componentes e prévias. Fotos selecionadas também são enviadas ao salvar uma edição existente. |
| Cadastro perdia o trabalho e não explicava a falha | Valores e arquivos mantidos após erros. Resumo com o campo e a mensagem retornados pela API; abertura da aba correspondente e foco no campo. Rascunho dos dados salvo por conta na sessão do navegador. |
| Obrigatoriedade pouco clara | Marcação dos campos obrigatórios, validação de limites e avisos navegáveis por aba. Campos de contagem vazios são normalizados para zero. |
| Galeria do iPhone e formatos de imagem | Seletor de arquivos acessível sobre a área de seleção. Backend valida e converte fotos HEIC/HEIF, JPEG, PNG e WebP para JPEG, aplica orientação, limita a dimensão e remove metadados EXIF. |
| Formulário público não recebia fotos | Inclusão de fotos opcionais via multipart, persistência vinculada ao lead e consulta no painel. Notificações incluem os links das fotos. |
| E-mail errado e sem ação | Rodapé e Contato usam `servenegociosimobiliarios@gmail.com` com `mailto:`. |
| WhatsApp fictício em Contato | Substituído por `(83) 9672-4745`, com link para WhatsApp. |
| SEO/Publicação difícil de entender | Aba renomeada para Publicação; explicação de Rascunho, Publicado e Destaque; campos para buscadores claramente opcionais. |
| Definição da capa falhava | Endpoint de edição de imagem passa a aceitar JSON, formato usado pelo frontend. |
| Erro de validação após renovar a sessão provocava logout | Tratamento da falha de renovação separado da validação da requisição repetida. Um 400 ao salvar preserva sessão e formulário. |

## Integridade dos envios

- Até 20 fotos por seleção/envio, somando no máximo 10 MiB. Rejeição mantém a seleção anterior.
- Todo o lote é validado antes de salvar fotos. Falhas de gravação revertem o lote e removem os arquivos já gravados nessa tentativa.
- Fotos novas são acrescentadas à ordem existente.
- A chave de idempotência da oferta considera os campos e o conteúdo dos anexos: repetir o envio não duplica lead, fotos ou notificação.
- Falha de e-mail não elimina a oferta. O reenvio administrativo permanece disponível.
- Rascunhos de texto duram a sessão da aba e são limpos no logout. Por restrição dos navegadores, arquivos locais não são restaurados após recarregar; a interface informa que precisam ser selecionados novamente. Alternar abas do formulário preserva os arquivos.

## Validação

- 48 testes automatizados do backend aprovados, incluindo 9 novos testes de anexos, conversão HEIC, idempotência, falhas de lote, ordem, capa por JSON e exclusão.
- Build Angular de produção aprovado.
- `manage.py check`, `makemigrations --check --dry-run` e `git diff --check` sem pendências.
- Regressão ponta a ponta aprovada em Chromium desktop (1440 × 900) e WebKit móvel (390 × 844), com API real e banco local descartável. Em cada navegador: botão visível antes/depois de scroll e acima de controles sobrepostos; oferta com seleção cumulativa de fotos; contatos clicáveis; navegação administrativa; validação sem perder texto/anexos; cadastro e publicação; definição de capa; recuperação de rascunho; renovação de sessão seguida de erro de validação.

Os testes de WebKit simulam tela e toque; não equivalem a um teste em iPhone físico com o seletor nativo da galeria. E-mails foram validados com backend de e-mail em memória, sem envio a pessoas reais. Não foi realizado deploy nem teste com dados da VPS.

## Reproduzir os testes

Com Python 3.12 e Node compatível com Angular 20:

```bash
python -m pip install -r back-end/requirements.txt
python back-end/manage.py test apps --settings=config.test_settings
cd front-end
npm ci
npx playwright install --with-deps chromium webkit
npm run test:e2e
```

`test:e2e` compila a produção e inicia API e frontend locais com banco, mídia e conta de teste descartáveis. Não usa dados de produção. O script de navegador rejeita URLs fora de localhost.

## Atualizar a VPS

A mudança adiciona a migração `leads.0003_leadimage` e a dependência `pillow-heif`. Rebuild do backend e do frontend é necessário. O Compose de produção existente já executa as migrações ao iniciar a API.

Na pasta do projeto, com o arquivo de ambiente de produção existente:

```bash
git pull origin main
docker compose --env-file back-end/.env.production -f docker-compose.production.yml up --build -d
```

O comando mantém os volumes existentes. A configuração Nginx versionada já permite requisições de até 12 MiB, compatíveis com o limite de fotos da aplicação. Confirmar em produção o envio SMTP e a galeria de um iPhone físico após o rebuild.
