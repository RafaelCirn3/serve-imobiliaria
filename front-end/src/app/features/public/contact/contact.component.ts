import { SiteContentService } from '@core/services/site-content.service';
import { SiteSectionDirective } from '@shared/components/site-section.directive';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { LeadService } from '@core/services/lead.service';
import { NotificationService } from '@core/services/notification.service';
import { FooterComponent } from '@shared/components/footer.component';
import { HeaderComponent } from '@shared/components/header.component';

@Component({
  selector: 'app-contact',
  standalone: true,
  imports: [SiteSectionDirective, ReactiveFormsModule, HeaderComponent, FooterComponent],
  template: `
    <div class="page-shell">
      <app-header />
      <main class="section container" data-site-page="contact">
        <div appSiteSection="contact.intro"><span class="eyebrow">{{site.text('contact','label')}}</span>
        <h1 class="section-title">{{site.text('contact','title')}}</h1></div>
        <div class="grid">
          <form appSiteSection="contact.form" class="card" [formGroup]="form" (ngSubmit)="submit()">
            <input formControlName="nome" [placeholder]="site.text('contact','name_placeholder')">
            <input formControlName="email" [placeholder]="site.text('contact','email_placeholder')">
            <input formControlName="telefone" [placeholder]="site.text('contact','phone_placeholder')">
            <textarea formControlName="mensagem" [placeholder]="site.text('contact','message_placeholder')"></textarea>
            <button class="btn btn-primary" type="submit" [disabled]="form.invalid">{{site.text('contact','submit_label')}}</button>
          </form>
          <aside appSiteSection="contact.details" class="card info" id="proprietarios">
            <h2>{{site.text('contact','direct_title')}}</h2>
            <p><a [href]="site.whatsapp()" target="_blank" rel="noopener noreferrer">WhatsApp: {{site.text('general','phone_label')}}</a></p>
            <p>E-mail: <a [href]="'mailto:'+site.text('general','email')">{{site.text('general','email')}}</a></p>
            <p>Endereço: {{site.text('general','address')}}</p>
            <p>Instagram: {{site.text('general','instagram')}}</p>
            <hr>
            <h3>{{site.text('contact','owner_title')}}</h3>
            <p>{{site.text('contact','owner_body')}}</p>
          </aside>
        </div>
      </main>
      <app-footer />
    </div>
  `,
  styles: [`
    .grid {
      order: 2;
      display: grid;
      grid-template-columns: 1fr 0.7fr;
      gap: 24px;
      margin-top: 24px;
    }

    form,
    .info {
      display: grid;
      gap: 12px;
      padding: 24px;
    }

    input,
    textarea {
      border: 1px solid #30363d;
      border-radius: 8px;
      background: #12161a;
      color: #f5f5f5;
      padding: 12px;
    }

    textarea {
      min-height: 150px;
    }

    p {
      color: #b8b8b8;
    }

    hr {
      width: 100%;
      border: 0;
      border-top: 1px solid #30363d;
    }

    @media (max-width: 840px) {
      .grid {
      order: 2;
        grid-template-columns: 1fr;
      }
    }
  `],
})
export class ContactComponent { readonly site=inject(SiteContentService);
  private readonly fb = inject(FormBuilder);
  private readonly leads = inject(LeadService);
  private readonly notification = inject(NotificationService);

  readonly form = this.fb.nonNullable.group({
    nome: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    telefone: ['', Validators.required],
    mensagem: ['Gostaria de falar com a SERVE.', Validators.required],
  });

  submit(): void {
    if (this.form.invalid) {
      return;
    }
    this.leads.createLead({ ...this.form.getRawValue(), origem: 'formulario' }).subscribe({
      next: () => {
        this.notification.show({ type: 'success', text: 'Mensagem enviada com sucesso.' });
        this.form.reset({ mensagem: 'Gostaria de falar com a SERVE.' });
      },
      error: () => this.notification.show({ type: 'error', text: 'Não foi possível enviar a mensagem.' }),
    });
  }
}


