// Run against an isolated local database. This script creates test properties and leads.
import assert from 'node:assert/strict';
import { chromium, webkit } from 'playwright';
const base = process.env.E2E_BASE_URL || 'http://127.0.0.1:4200';
assert(['127.0.0.1', 'localhost'].includes(new URL(base).hostname), 'Use a local isolated test server.');
const username = process.env.E2E_USERNAME;
const password = process.env.E2E_PASSWORD;
assert(username && password, 'Set E2E_USERNAME and E2E_PASSWORD for a local staff account.');
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1sAAAAASUVORK5CYII=', 'base64');
const photo = name => ({ name, mimeType: 'image/png', buffer: png });
const results = [];
for (const [name, engine, options] of [
  ['desktop-chromium', chromium, { viewport: { width: 1440, height: 900 } }],
  ['mobile-webkit', webkit, { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 3 }],
]) {
 const browser = await engine.launch({ headless: true });
 const context = await browser.newContext(options);
 const page = await context.newPage();
 const errors = [];
 page.on('pageerror', error => errors.push(error.message));
 const field = name => page.locator(`[formControlName="${name}"]:visible`).last();
 const tab = label => page.locator('nav.tabs button').filter({ hasText: label }).click();
 try {
  await page.goto(base);
  const cta = page.locator('.sale-trigger');
  await cta.waitFor({ state: 'visible' });
  const before = await cta.boundingBox();
  assert(before && before.y > 0 && before.y + before.height <= options.viewport.height);
  await page.evaluate(() => {
    const button = document.querySelector('.sale-trigger');
    const r = button.getBoundingClientRect();
    const input = document.createElement('input'); input.id = 'overlap-probe';
    Object.assign(input.style, { position: 'fixed', left: `${r.left}px`, top: `${r.top}px`, width: `${r.width}px`, height: `${r.height}px`, zIndex: '999999' });
    document.body.append(input);
  });
  assert(await cta.evaluate(button => { const r = button.getBoundingClientRect(); return document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2) === button; }));
  await page.evaluate(() => document.querySelector('#overlap-probe').remove());
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);
  assert(Math.abs((await cta.boundingBox()).y - before.y) < 2);
  await cta.click();
  await page.locator('dialog[open]').waitFor();
  await page.getByRole('button', { name: 'Enviar imóvel', exact: true }).click();
  assert(await page.getByText('Informe seu nome.').isVisible());
  await field('nome').fill('Teste proprietário'); await field('email').fill('owner@example.test');
  await field('telefone').fill('83999998888'); await field('mensagem').fill('Oferta com duas fotos');
  await field('finalidade').selectOption('aluguel');
  await page.locator('input[type=file]').setInputFiles(photo('offer1.png'));
  await page.locator('input[type=file]').setInputFiles(photo('offer2.png'));
  assert.equal(await page.locator('app-image-uploader figure').count(), 2);
  const offerResponse = page.waitForResponse(r => r.url().endsWith('/leads/venda-imovel/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Enviar imóvel', exact: true }).click();
  const offer = await offerResponse; assert.equal(offer.status(), 201, await offer.text());
  await page.getByText('Solicitação registrada!', { exact: true }).waitFor();
  const offerId = (await offer.json()).id;
  await page.getByRole('button', { name: 'Concluir', exact: true }).click();
  await page.goto(base + '/contato');
  assert.equal(await page.locator('a[href="mailto:servenegociosimobiliarios@gmail.com"]').count(), 2);
  assert(await page.getByText('WhatsApp: (83) 9672-4745').first().isVisible());
  await page.goto(base + '/admin/login');
  await field('email').fill(username); await field('password').fill(password);
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await page.waitForURL('**/admin/dashboard');
  if (name.startsWith('mobile')) await page.getByRole('button', { name: 'Menu administrativo' }).click();
  await page.locator('#admin-navigation a[routerLink="/admin/imoveis"]').click();
  await page.getByRole('link', { name: 'Novo imóvel', exact: true }).click();
  await page.getByRole('button', { name: 'Salvar', exact: true }).click();
  assert(await page.locator('.error-summary').isVisible());
  await field('titulo').fill(`Verificação ${name} ${Date.now()}`);
  await field('valor').fill('250000.50'); await field('descricao').fill('Descrição preservada entre abas');
  await tab('Localização'); await field('bairro').fill('Centro');
  await field('cep').fill('123');
  await tab('Fotos');
  await page.locator('input[type=file]').setInputFiles(photo('admin1.png'));
  await page.locator('input[type=file]').setInputFiles(photo('admin2.png'));
  await tab('Informações básicas');
  assert.equal(await field('descricao').inputValue(), 'Descrição preservada entre abas');
  await tab('Fotos'); assert.equal(await page.locator('app-image-uploader figure').count(), 2);
  // Backend validation must expose CEP, preserve text/photos, and open the location tab.
  const badSave = page.waitForResponse(r => r.url().endsWith('/admin/imoveis/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Salvar', exact: true }).click();
  assert.equal((await badSave).status(), 400);
  assert(await field('cep').isVisible()); assert(await page.locator('.error-summary').getByText(/CEP/).isVisible());
  await field('cep').fill('');
  await tab('Publicação'); await field('status').selectOption('publicado'); await field('destaque').check();
  await page.getByRole('button', { name: 'Salvar', exact: true }).click();
  await page.waitForURL(/\/admin\/imoveis\/\d+\/editar$/);
  await tab('Fotos');
  await page.locator('figcaption button').filter({ hasText: 'Definir capa' }).first().waitFor();
  assert.equal(await page.locator('app-image-uploader figure').count(), 2);
  const cover = page.waitForResponse(r => /\/imagens\/\d+\/$/.test(r.url()) && r.request().method() === 'PATCH');
  await page.getByRole('button', { name: 'Definir capa', exact: true }).first().click();
  assert.equal((await cover).status(), 200);
  await page.getByRole('button', { name: 'Capa atual', exact: true }).waitFor();
  await tab('Informações básicas');
  await field('descricao').fill('Alteração recuperável'); await page.reload();
  await page.getByText(/Rascunho recuperado neste navegador/).waitFor();
  assert.equal(await field('descricao').inputValue(), 'Alteração recuperável');
  const token = await page.evaluate(() => localStorage.getItem('serve_access_token'));
  const lead = await context.request.get(`${base}/api/admin/leads/${offerId}/`, { headers: { Authorization: `Bearer ${token}` } });
  assert.equal((await lead.json()).fotos.length, 2);
  // A 400 following successful refresh must keep the session and entered data.
  await page.evaluate(() => localStorage.setItem('serve_access_token', 'expired-test-token'));
  await tab('Localização'); await field('cep').fill('123');
  const retry = page.waitForResponse(r => /\/admin\/imoveis\/\d+\/$/.test(r.url()) && r.status() === 400);
  await page.getByRole('button', { name: 'Salvar', exact: true }).click(); await retry;
  assert(!page.url().endsWith('/login'));
  assert(await page.evaluate(() => !!localStorage.getItem('serve_access_token')));
  assert(await page.locator('.error-summary').getByText(/CEP/).isVisible());
  await tab('Informações básicas'); assert.equal(await field('descricao').inputValue(), 'Alteração recuperável');
  assert.deepEqual(errors, []);
  results.push({ browser: name, status: 'PASS', checks: ['CTA before/after scroll and stacking', 'public offer with cumulative photos', 'contact links', 'admin navigation', 'validation preserves data/photos', 'create and publish', 'cover JSON update', 'draft reload', 'token refresh then validation'] });
 } finally { await browser.close(); }
}
console.log(JSON.stringify(results, null, 2));
