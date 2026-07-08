import { Component } from '@angular/core';
import { FooterComponent } from '@shared/components/footer.component';
import { HeaderComponent } from '@shared/components/header.component';

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [HeaderComponent, FooterComponent],
  template: `
    <div class="page-shell">
      <app-header />
      <main>
        <section class="hero">
          <div class="container">
            <span class="eyebrow">Sobre a SERVE</span>
            <h1>Uma rede imobiliária enxuta, premium e focada em João Pessoa.</h1>
          </div>
        </section>
        <section class="section container split">
          <div>
            <h2 class="section-title">Curadoria, presenca local e atendimento direto.</h2>
            <p>A SERVE nasce para organizar a jornada imobiliária em João Pessoa com menos ruído e mais critério. Nesta fase, a gestão dos imóveis é centralizada pelo administrador da marca.</p>
            <p>O foco está nas regiões mais valorizadas da cidade, da orla aos bairros em expansão, sempre com apresentação visual forte e informação objetiva.</p>
          </div>
          <div class="card values">
            <strong>Diferenciais</strong>
            <span>Leitura local de mercado</span>
            <span>Imóveis apresentados com padrão premium</span>
            <span>Contato rapido com interessados qualificados</span>
            <span>Conteúdo claro para compra, venda e locação</span>
          </div>
        </section>
      </main>
      <app-footer />
    </div>
  `,
  styles: [`
    .hero {
      min-height: 460px;
      display: grid;
      align-items: end;
      padding: 90px 0 64px;
      background:
        linear-gradient(180deg, rgba(17, 20, 23, 0.12), #111417),
        linear-gradient(90deg, rgba(17, 20, 23, 0.88), rgba(17, 20, 23, 0.24)),
        url('https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1800&q=85') center/cover;
    }

    h1 {
      max-width: 860px;
      margin: 12px 0 0;
      font-size: clamp(2.5rem, 6vw, 5.4rem);
      line-height: 0.98;
    }

    .split {
      display: grid;
      grid-template-columns: 1fr 0.75fr;
      gap: 28px;
      align-items: center;
    }

    p,
    span {
      color: #b8b8b8;
      line-height: 1.8;
    }

    .values {
      display: grid;
      gap: 14px;
      padding: 26px;
    }

    strong {
      color: #d6b765;
      font-size: 1.2rem;
    }

    @media (max-width: 860px) {
      .split {
        grid-template-columns: 1fr;
      }
    }
  `],
})
export class AboutComponent {}
