import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { LeadService } from '@core/services/lead.service';
import { NotificationService } from '@core/services/notification.service';
import { FooterComponent } from '@shared/components/footer.component';
import { HeaderComponent } from '@shared/components/header.component';

@Component({
  selector: 'app-contact',
  standalone: true,
  imports: [ReactiveFormsModule, HeaderComponent, FooterComponent],
  template: `
    <div class="page-shell">
      <app-header />
      <main class="section container">
        <span class="eyebrow">Contato</span>
        <h1 class="section-title">Fale com a SERVE</h1>
        <div class="grid">
          <form class="card" [formGroup]="form" (ngSubmit)="submit()">
            <input formControlName="nome" placeholder="Nome">
            <input formControlName="email" placeholder="Email">
            <input formControlName="telefone" placeholder="Telefone">
            <textarea formControlName="mensagem" placeholder="Como podemos ajudar?"></textarea>
            <button class="btn btn-primary" type="submit" [disabled]="form.invalid">Enviar</button>
          </form>
          <aside class="card info" id="proprietarios">
            <h2>Atendimento direto</h2>
            <p>WhatsApp: (83) 99999-9999</p>
            <p>Email: contato&#64;serveimoveis.com.br</p>
            <p>Endereço: João Pessoa/PB</p>
            <p>Instagram: &#64;serveimoveis</p>
            <hr>
            <h3>Para proprietários</h3>
            <p>Envie os dados do seu imóvel para avaliarmos a apresentação e a estratégia de divulgação.</p>
          </aside>
        </div>
      </main>
      <app-footer />
    </div>
  `,
  styles: [`
    .grid {
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
        grid-template-columns: 1fr;
      }
    }
  `],
})
export class ContactComponent {
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
