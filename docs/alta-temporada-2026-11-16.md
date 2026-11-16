# Correções para a alta temporada — 16/11/2026

- Logo oficial SERVE by JB convertida do CGM para SVG transparente, sem alterar as formas vetoriais. O arquivo padrão está em `front-end/src/assets/serve-official.svg`; logotipos personalizados continuam disponíveis no editor.
- A chamada para proprietários aparece dentro do hero na home e usa o mesmo formulário existente. Nas demais páginas permanece o atalho flutuante.
- O carrossel principal alterna entre slides ativos, por padrão a cada 3 s. Em **Dashboard > Customização > Início > Textos e identidade**, altere o intervalo (1 a 60 segundos) e salve. Cadastre pelo menos dois slides ativos para haver rotação.
- Garagem rotativa é um indicador booleano independente da quantidade de vagas; os imóveis anteriores continuam com o valor numérico e modalidade não rotativa.
- Lançamento está disponível no cadastro, catálogo e filtros. A migração `properties.0007_rotating_parking_launch` acrescenta o campo sem eliminar dados.

## Publicação

Após a integração na main, na pasta do projeto na VPS:

    git pull --ff-only origin main
    docker compose -f docker-compose.production.yml up --build -d
    docker compose -f docker-compose.production.yml exec api python manage.py showmigrations properties

O serviço API aplica as migrações na inicialização. Confirme que a migração 0007 está marcada, verifique os logs e teste a home, busca e cadastro.

## Verificação local

    cd back-end
    python manage.py test --settings=config.test_settings
    python manage.py makemigrations --check --dry-run --settings=config.test_settings
    cd ../front-end
    npm ci
    npm run build
    python tests/run-local.py

Se o host não oferecer as bibliotecas do WebKit, use `E2E_MOBILE_CHROMIUM=1` para testar o viewport mobile no Chromium. Isso não substitui a homologação em Safari/iPhone real.
