import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { BrandComponent } from './brand.component';

@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [RouterLink, BrandComponent],
  template: `
    <footer>
      <div class="container footer-grid">
        <div>
          <app-brand />
          <small class="footer-creci">RESP CRECI 15202</small>
          <p>Curadoria imobiliária em João Pessoa, Cabedelo e Bananeiras, com foco em localização e atendimento direto.</p>
        </div>
        <div>
          <strong>Navegação</strong>
          <a routerLink="/imoveis">Imóveis</a>
          <a routerLink="/sobre">Sobre</a>
          <a routerLink="/contato">Contato</a>
        </div>
        <div>
          <strong>Contato</strong>
          <span>WhatsApp: (83) 99999-9999</span>
          <span>contato&#64;serveimoveis.com.br</span>
          <span>Atendimento em João Pessoa, Cabedelo e Bananeiras/PB</span>
        </div>
      </div>
    </footer>
  `,
  styles: [`
    footer {
      border-top: 1px solid #30363d;
      background: #0d1013;
      padding: 44px 0;
    }

    .footer-grid {
      display: grid;
      grid-template-columns: 1.5fr 1fr 1fr;
      gap: 28px;
    }

    p,
    span,
    a {
      color: #b8b8b8;
      line-height: 1.7;
    }

    .footer-creci {
      display: block;
      margin: 8px 0 14px;
      color: #ffffff;
      font-size: 0.72rem;
      font-weight: 800;
      letter-spacing: 0.08em;
    }

    strong {
      display: block;
      margin-bottom: 12px;
      color: #fff;
    }

    a,
    span {
      display: block;
      margin: 6px 0;
    }

    @media (max-width: 760px) {
      .footer-grid {
        grid-template-columns: 1fr;
      }
    }
  `],
})
export class FooterComponent {}


