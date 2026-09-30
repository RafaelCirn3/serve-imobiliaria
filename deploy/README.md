# Deploy da SERVE na EC2 + Cloudflare

Domínio principal: `servenegociosimobiliarios.com.br`  
Alias com redirecionamento 301: `serveimoveisjp.com.br`

## DNS no Cloudflare

Crie registros `A` apontando para o Elastic IP da EC2 para `@` e `www` nos dois domínios, com proxy habilitado. Use SSL/TLS em **Full (strict)**.

## Preparação da EC2 Amazon Linux

```bash
sudo dnf update -y
sudo dnf install -y docker git nginx
sudo systemctl enable --now docker nginx
sudo usermod -aG docker "$USER"
```

Libere no Security Group somente TCP 80, TCP 443 e SSH 22 restrito ao seu IP. Não libere 5432, 8000 ou 8080.

## Configuração

```bash
git clone https://github.com/RafaelCirn3/serve-imobiliaria serve
cd serve
cp back-end/.env.production.example back-end/.env.production
nano back-end/.env.production
```

Preencha `SECRET_KEY` e `POSTGRES_PASSWORD` com valores fortes e únicos.

## HTTPS e Nginx

O arquivo `deploy/nginx/servenegociosimobiliarios.conf` redireciona `serveimoveisjp.com.br` para o domínio principal e encaminha `/api/` e `/media/` para o backend.

O certificado deve cobrir os dois domínios e estar nos caminhos configurados no arquivo Nginx. Depois:

```bash
sudo cp deploy/nginx/servenegociosimobiliarios.conf /etc/nginx/conf.d/servenegociosimobiliarios.conf
sudo nginx -t
sudo systemctl reload nginx
```

## Subida da aplicação

```bash
docker compose -f docker-compose.production.yml up -d --build
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs -f api
```

O frontend fica em `127.0.0.1:8080` e a API em `127.0.0.1:8000`; o acesso público passa pelo Nginx.

## Verificação

```bash
curl -I https://servenegociosimobiliarios.com.br/
curl -I https://serveimoveisjp.com.br/
curl -I https://servenegociosimobiliarios.com.br/api/imoveis/
```

O segundo domínio deve responder com `301` para o domínio principal. O frontend publica canonical, Open Graph, `robots.txt` e `sitemap.xml` apontando para `servenegociosimobiliarios.com.br`.
