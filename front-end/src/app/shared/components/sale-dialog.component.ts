import { Component, ElementRef, HostListener, OnDestroy, afterNextRender, effect, inject, signal, viewChild } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { PROPERTY_TYPES, SERVICE_CITIES } from '@core/models/property-options';
import { LeadService } from '@core/services/lead.service';
import { SaleDialogService } from '@core/services/sale-dialog.service';
import { AddressEditorComponent } from './address-editor.component';

@Component({
  selector: 'app-sale-dialog', standalone: true, imports: [ReactiveFormsModule, AddressEditorComponent],
  template: `
    <div class="sale-actions" [class.avoid-controls]="floatingHidden()" [style.--floating-offset]="floatingBottom() + 'px'"><a class="sale-whatsapp" href="https://wa.me/558396724745?text=Ol%C3%A1%2C%20quero%20vender%20meu%20im%C3%B3vel." target="_blank" rel="noopener noreferrer" aria-label="Conversar no WhatsApp sobre venda de imóvel"><svg viewBox="0 0 32 32" width="24" height="24" aria-hidden="true"><path fill="currentColor" d="M16 2a14 14 0 0 0-12 21L2 30l7.3-2A14 14 0 1 0 16 2Zm0 25a11 11 0 0 1-5.7-1.6l-.5-.3-4 1.1L7 22.3l-.3-.5A11 11 0 1 1 16 27Zm6-8c-.3-.2-1.9-1-2.2-1.1-.3-.1-.5-.1-.7.2-.2.3-.9 1.1-1.1 1.2-.2.2-.4.2-.7.1-1.9-.9-3.2-2.2-4.1-3.9-.2-.3 0-.5.1-.7l.6-.6c.2-.2.3-.4.4-.6.1-.2 0-.4 0-.6L13.2 10c-.3-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.3-1.1 1.1-1.1 2.7s1.2 3.2 1.4 3.4c.2.2 2.4 3.7 5.8 5.1.8.3 1.5.5 2 .6.8.1 2.3-1 2.6-1.9.2-.8.2-1.5.1-1.6-.1-.1-.3-.2-.6-.4Z"/></svg></a><button #trigger type="button" class="sale-trigger" (click)="dialogService.open()" aria-haspopup="dialog">Quer vender seu imóvel? Descreva aqui!</button></div>
    <dialog #dialog aria-labelledby="sale-title" (cancel)="dialogService.close()" (close)="dialogService.close()">
      <div class="dialog-header">
        <div><span class="eyebrow">Para proprietários</span><h2 id="sale-title">Conte sobre seu imóvel</h2></div>
        <button type="button" class="close" aria-label="Fechar formulário" (click)="dialogService.close()">×</button>
      </div>
      @if (success) {
        <div role="status" class="success"><h3>Solicitação registrada!</h3><p>{{ success }}</p>
          <button class="btn btn-primary" type="button" (click)="dialogService.close()">Concluir</button>
        </div>
      } @else {
        <p class="intro">Descreva seu imóvel. A SERVE usará seus dados para retornar o contato e avaliar a oferta.</p>
        <form [formGroup]="form" (ngSubmit)="submit()">
          <fieldset [disabled]="sending">
            <div class="fields">
              <label>Nome *<input autofocus autocomplete="name" formControlName="nome" maxlength="120">@if (invalid('nome')) { <small>Informe seu nome.</small> }</label>
              <label>E-mail *<input type="email" autocomplete="email" formControlName="email" maxlength="254">@if (invalid('email')) { <small>Informe um e-mail válido.</small> }</label>
              <label>Telefone/WhatsApp *<input type="tel" autocomplete="tel" formControlName="telefone" maxlength="30">@if (invalid('telefone')) { <small>Informe um telefone com DDD.</small> }</label>
              <label>Tipo de imóvel<select formControlName="tipo"><option value="">Selecione</option>@for (type of propertyTypes; track type.value) { <option [value]="type.value">{{ type.label }}</option> }</select></label>
              <app-address-editor [form]="form" listId="sale-address" />
              <label>Quartos<input type="number" min="0" step="1" formControlName="quartos"></label>
              <label>Área total (m²)<input type="number" min="0" step="0.01" formControlName="area_total"></label>
              <label>Valor pretendido (R$)<input type="number" min="0" step="0.01" formControlName="valor"></label>
              <label class="full">Descrição *<textarea formControlName="mensagem" rows="4" maxlength="5000" placeholder="Conte o que torna seu imóvel especial."></textarea>@if (invalid('mensagem')) { <small>Descreva seu imóvel (até 5.000 caracteres).</small> }</label>
            </div>
            <label class="honeypot" aria-hidden="true">Website<input formControlName="website" tabindex="-1" autocomplete="off"></label>
            @if (error) { <p class="error" role="alert">{{ error }}</p> }
            @if (submitted && form.invalid) { <p class="error" role="alert">Revise os campos obrigatórios e use valores não negativos.</p> }
            <button type="submit" class="btn btn-primary" [disabled]="sending">{{ sending ? 'Registrando…' : 'Enviar imóvel' }}</button>
          </fieldset>
        </form>
      }
    </dialog>
  `,
  styles: [`
    .sale-actions { position: fixed; right: max(20px, env(safe-area-inset-right)); bottom: max(var(--floating-offset, 20px), env(safe-area-inset-bottom)); z-index: 90; display: grid; justify-items: center; gap: 8px; }
    .sale-whatsapp { display: inline-flex; align-items: center; gap: 8px; min-height: 44px; border-radius: 999px; padding: 8px 15px; background: #16873b; color: white; font-weight: 800; box-shadow: 0 6px 20px #0006; }
    .sale-actions.avoid-controls { visibility: hidden; pointer-events: none; }
    .sale-trigger { max-width: calc(100vw - 32px); border: 1px solid #ffffff50; border-radius: 28px; background: #f5f5f5; color: #111417; padding: 14px 20px; font-weight: 800; box-shadow: 0 6px 28px #0006; }

    dialog { width: min(720px, calc(100vw - 32px)); max-height: calc(100dvh - 32px); overflow: auto; color: #f5f5f5; background: #181c20; border: 1px solid #ffffff30; border-radius: 16px; padding: 24px; }
    dialog::backdrop { background: #000b; backdrop-filter: blur(4px); }
    .dialog-header { display: flex; align-items: start; justify-content: space-between; gap: 16px; }
    h2 { margin: 8px 0; } .intro { color: #b8b8b8; line-height: 1.6; }
    .close { background: transparent; border: 0; color: white; font-size: 30px; min-width: 44px; min-height: 44px; }
    .fields { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .full { grid-column: 1 / -1; } label { display: grid; gap: 7px; font-size: .9rem; }
    input, select, textarea { min-width: 0; width: 100%; border: 1px solid #ffffff30; border-radius: 8px; background: #111417; color: #f5f5f5; padding: 12px; }
    textarea { resize: vertical; } fieldset { border: 0; padding: 0; margin: 0; min-width: 0; } small, .error { color: #ffb4b4; }
    .honeypot { position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden; }
    form .btn { margin-top: 20px; } .success { padding: 20px 0; line-height: 1.6; }
    :focus-visible { outline: 2px solid #fff; outline-offset: 3px; }
    @media(max-width:560px) { .fields { grid-template-columns: 1fr; } dialog { padding: 18px; } .sale-trigger { font-size: .8rem; padding: 12px 16px; } }
  `],
})
export class SaleDialogComponent implements OnDestroy {
  readonly dialogService = inject(SaleDialogService);
  private readonly leads = inject(LeadService);
  private readonly fb = inject(FormBuilder);
  private readonly dialog = viewChild<ElementRef<HTMLDialogElement>>('dialog');
  private readonly trigger = viewChild<ElementRef<HTMLButtonElement>>('trigger');
  readonly propertyTypes = PROPERTY_TYPES;
  readonly cities = SERVICE_CITIES;
  sending = false; submitted = false; error = ''; success = '';
  readonly floatingHidden = signal(false);
  readonly floatingBottom = signal(20);
  private frame = 0;
  private contentObserver?: MutationObserver;
  private layoutObserver?: ResizeObserver;
  private previousOverflow = '';
  private locked = false;
  private requestKey = '';
  private requestBody = '';
  readonly form = this.fb.nonNullable.group({
    nome: ['', [Validators.required, Validators.pattern(/\S/), Validators.maxLength(120)]],
    email: ['', [Validators.required, Validators.email, Validators.maxLength(254)]],
    telefone: ['', [Validators.required, Validators.pattern(/^(?=(?:\D*[0-9]){10,15}\D*$)[0-9\s()+-]{10,30}$/)]],
    mensagem: ['', [Validators.required, Validators.pattern(/\S/), Validators.maxLength(5000)]],
    tipo: [''], cep: [''], cidade: [''], uf: ['PB'], bairro: [''], logradouro: [''], numero: [''], complemento: [''], website: [''],
    quartos: [null as number | null, [Validators.min(0), Validators.pattern(/^\d+$/)]],
    area_total: [null as number | null, Validators.min(0)], valor: [null as number | null, Validators.min(0)],
  });

  constructor() {
    afterNextRender(() => {
      this.contentObserver = new MutationObserver(() => this.scheduleOverlapCheck());
      this.contentObserver.observe(document.body, { childList: true, subtree: true });
      this.layoutObserver = new ResizeObserver(() => this.scheduleOverlapCheck());
      this.layoutObserver.observe(document.body);
      this.avoidOverlaps();
    });
    effect(() => {
      const element = this.dialog()?.nativeElement;
      if (!element) return;
      if (this.dialogService.opened() && !element.open) {
        if (this.success) { this.success = ''; this.form.reset(); this.submitted = false; this.requestBody = ''; this.requestKey = ''; }
        this.previousOverflow = document.body.style.overflow;
        this.locked = true; document.body.style.overflow = 'hidden'; element.showModal();
      } else if (!this.dialogService.opened()) {
        if (element.open) element.close();
        if (this.locked) { document.body.style.overflow = this.previousOverflow; this.locked = false; }
      }
    });
  }

  @HostListener('window:scroll')
  @HostListener('window:resize')
  scheduleOverlapCheck(): void {
    cancelAnimationFrame(this.frame);
    this.frame = requestAnimationFrame(() => this.avoidOverlaps());
  }

  private avoidOverlaps(): void {
    const button = this.trigger()?.nativeElement;
    if (!button) return;
    const actual = (button.closest('.sale-actions') ?? button).getBoundingClientRect();
    let rectangle = { left: actual.left, right: actual.right, top: innerHeight - 20 - actual.height, bottom: innerHeight - 20 };
    const intersects = (other: DOMRect) => other.width > 0 && other.height > 0 && rectangle.left < other.right && rectangle.right > other.left && rectangle.top < other.bottom && rectangle.bottom > other.top;
    let bottom = 20;
    for (const attribution of document.querySelectorAll('.leaflet-control-attribution')) {
      const bounds = attribution.getBoundingClientRect();
      if (intersects(bounds)) bottom = Math.max(bottom, innerHeight - bounds.top + 12);
    }
    rectangle = { ...rectangle, top: innerHeight - bottom - actual.height, bottom: innerHeight - bottom };
    this.floatingBottom.set(bottom);
    this.floatingHidden.set(document.activeElement !== button && Array.from(document.querySelectorAll('input, select, textarea, button, a, .leaflet-control'))
      .some((element) => element !== button && !element.closest('.sale-actions') && !element.closest('dialog') && intersects(element.getBoundingClientRect())));
  }
  invalid(field: string): boolean {
    const control = this.form.get(field);
    return Boolean(control?.invalid && (control.touched || this.submitted));
  }
  submit(): void {
    this.submitted = true; this.form.markAllAsTouched();
    if (this.form.invalid || this.sending) return;
    const payload = this.form.getRawValue();
    const body = JSON.stringify(payload);
    if (body !== this.requestBody) { this.requestBody = body; this.requestKey = crypto.randomUUID(); }
    this.sending = true; this.error = '';
    this.leads.offerProperty({ ...payload, idempotency_key: this.requestKey }).subscribe({
      next: (result) => {
        this.sending = false;
        this.success = result.notificacao_status === 'enviado'
          ? 'Sua oferta foi registrada e a SERVE foi notificada por e-mail. Aguarde nosso contato.'
          : 'Sua oferta foi registrada para atendimento. A notificação por e-mail está pendente; seus dados foram preservados.';
      },
      error: (response) => {
        this.sending = false;
        this.error = response.status === 429 ? 'Muitas tentativas. Aguarde alguns minutos antes de tentar novamente.' : 'Não foi possível registrar sua oferta. Confira os dados e tente novamente.';
      },
    });
  }
  ngOnDestroy(): void {
    cancelAnimationFrame(this.frame);
    this.contentObserver?.disconnect();
    this.layoutObserver?.disconnect();
    if (this.locked) document.body.style.overflow = this.previousOverflow;
    this.dialogService.close();
  }
}
