import { CurrencyPipe, Location } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { environment } from '@env/environment';
import { Property } from '@core/models/api.models';
import { LeadService } from '@core/services/lead.service';
import { NotificationService } from '@core/services/notification.service';
import { PropertyService } from '@core/services/property.service';
import { FooterComponent } from '@shared/components/footer.component';
import { HeaderComponent } from '@shared/components/header.component';
import { LoadingComponent } from '@shared/components/loading.component';
import { PropertyCardComponent } from '@shared/components/property-card.component';

@Component({
  selector: 'app-property-detail',
  standalone: true,
  imports: [CurrencyPipe, ReactiveFormsModule, HeaderComponent, FooterComponent, LoadingComponent, PropertyCardComponent],
  template: `
    <div class="page-shell">
      <app-header />
      @if (loading) {
        <app-loading />
      } @else if (property) {
        <main class="container detail">
          <button class="back-button" type="button" (click)="goBack()">← Voltar</button>
          <section class="gallery">
            <img class="main-image" [src]="mainImage" [alt]="property.titulo">
            <div class="thumbs">
              @for (image of property.imagens; track image.id) {
                <button type="button" [class.active]="mainImage === image.imagem" (click)="mainImage = image.imagem"><img [src]="image.imagem" [alt]="image.legenda || property.titulo"></button>
              }
            </div>
          </section>

          <section class="content">
            <div>
              <span class="eyebrow">{{ property.bairro }} · {{ property.cidade }}</span>
              <h1>{{ property.titulo }}</h1>
              <strong class="price">{{ numberValue(property.valor) | currency:'BRL':'symbol':'1.0-0':'pt-BR' }}</strong>
              <div class="features">
                <span>{{ property.quartos }} quartos</span>
                <span>{{ property.suites }} suítes</span>
                <span>{{ property.banheiros }} banheiros</span>
                <span>{{ property.vagas }} vagas</span>
                <span>{{ property.area_privativa || property.area_total }} m²</span>
              </div>
              <p class="description">{{ property.descricao }}</p>
              @if (property.latitude && property.longitude) {
                <div class="map card">
                  Localização aproximada: {{ property.latitude }}, {{ property.longitude }}
                </div>
              }
            </div>

            <aside class="lead-card card">
              <h2>Tenho interesse</h2>
              <form [formGroup]="leadForm" (ngSubmit)="sendLead()">
                <input formControlName="nome" placeholder="Nome">
                <input formControlName="email" placeholder="Email">
                <input formControlName="telefone" placeholder="Telefone">
                <textarea formControlName="mensagem" placeholder="Mensagem"></textarea>
                <button class="btn btn-primary" type="submit" [disabled]="leadForm.invalid">Enviar interesse</button>
              </form>
              <a class="btn btn-secondary whatsapp" [href]="whatsappLink" target="_blank">Chamar no WhatsApp</a>
            </aside>
          </section>

          @if (similar.length) {
            <section class="section">
              <h2>Imóveis semelhantes</h2>
              <div class="similar-grid">
                @for (item of similar; track item.id) {
                  <app-property-card [property]="item" />
                }
              </div>
            </section>
          }
        </main>
      }
      <app-footer />
    </div>
  `,
  styles: [`
    .detail {
      padding: 40px 0 0;
    }

    .back-button {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 42px;
      border: 1px solid rgba(201, 162, 74, 0.4);
      border-radius: 999px;
      background: rgba(201, 162, 74, 0.08);
      color: #d6b765;
      font-weight: 900;
      padding: 0 16px;
      margin-bottom: 18px;
      transition: background 0.18s ease, transform 0.18s ease;
    }

    .back-button:hover {
      background: rgba(201, 162, 74, 0.16);
      transform: translateX(-2px);
    }

    .gallery {
      display: grid;
      gap: 12px;
      animation: fadeUp 0.45s ease both;
    }

    .main-image {
      width: 100%;
      height: min(620px, 62vw);
      min-height: 320px;
      object-fit: cover;
      border-radius: 8px;
      transition: opacity 0.2s ease;
    }

    .thumbs {
      display: flex;
      gap: 10px;
      overflow-x: auto;
    }

    .thumbs button {
      border: 1px solid #30363d;
      border-radius: 8px;
      background: transparent;
      padding: 0;
      overflow: hidden;
      min-width: 120px;
      opacity: 0.72;
      transition: border-color 0.18s ease, opacity 0.18s ease, transform 0.18s ease;
    }

    .thumbs button:hover,
    .thumbs button.active {
      border-color: #c9a24a;
      opacity: 1;
      transform: translateY(-1px);
    }

    .thumbs img {
      width: 120px;
      height: 82px;
      object-fit: cover;
    }

    .content {
      display: grid;
      grid-template-columns: 1fr 360px;
      gap: 32px;
      margin-top: 34px;
      animation: fadeUp 0.5s ease both;
      animation-delay: 0.08s;
    }

    h1 {
      margin: 10px 0 14px;
      font-size: clamp(2rem, 5vw, 4rem);
      line-height: 1.04;
    }

    .price {
      color: #d6b765;
      font-size: 2rem;
    }

    .features {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 22px 0;
    }

    .features span {
      border: 1px solid #30363d;
      border-radius: 999px;
      color: #b8b8b8;
      padding: 8px 12px;
    }

    .description {
      color: #d8d8d8;
      line-height: 1.8;
    }

    .map,
    .lead-card {
      padding: 20px;
    }

    .lead-card {
      position: sticky;
      top: 98px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.18);
    }

    form {
      display: grid;
      gap: 10px;
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
      min-height: 110px;
    }

    .whatsapp {
      width: 100%;
      margin-top: 10px;
    }

    .similar-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
    }

    @media (max-width: 900px) {
      .content,
      .similar-grid {
        grid-template-columns: 1fr;
      }

      .lead-card {
        position: static;
      }

      .detail {
        padding-top: 22px;
      }

      .main-image {
        min-height: 260px;
      }

      .thumbs {
        padding-bottom: 4px;
        scroll-snap-type: x proximity;
      }

      .thumbs button {
        scroll-snap-align: start;
      }
    }

    @keyframes fadeUp {
      from {
        opacity: 0;
        transform: translateY(14px);
      }

      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `],
})
export class PropertyDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  private readonly propertyService = inject(PropertyService);
  private readonly leadService = inject(LeadService);
  private readonly notification = inject(NotificationService);
  private readonly location = inject(Location);

  property: Property | null = null;
  similar: Property[] = [];
  mainImage = '';
  loading = true;

  readonly leadForm = this.fb.nonNullable.group({
    nome: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    telefone: ['', Validators.required],
    mensagem: ['Tenho interesse neste imóvel.'],
  });

  ngOnInit(): void {
    const slug = this.route.snapshot.paramMap.get('slug') || '';
    this.propertyService.getPropertyBySlug(slug).subscribe({
      next: (property) => {
        this.property = property;
        this.mainImage = property.imagens?.[0]?.imagem || 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1600&q=85';
        this.loading = false;
        this.loadSimilar(property);
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  get whatsappLink(): string {
    const text = encodeURIComponent(`Olá, tenho interesse no imóvel ${this.property?.titulo}`);
    return `https://wa.me/${environment.whatsappNumber}?text=${text}`;
  }

  numberValue(value: string | number): number {
    return Number(value || 0);
  }

  goBack(): void {
    if (window.history.length > 1) {
      this.location.back();
      return;
    }
    window.location.href = '/imoveis';
  }

  sendLead(): void {
    if (!this.property || this.leadForm.invalid) {
      return;
    }

    this.leadService.createLead({
      ...this.leadForm.getRawValue(),
      imovel: this.property.id,
      origem: 'formulario',
    }).subscribe({
      next: () => {
        this.notification.show({ type: 'success', text: 'Interesse enviado. A SERVE entrará em contato.' });
        this.leadForm.reset({ mensagem: 'Tenho interesse neste imóvel.' });
      },
      error: () => this.notification.show({ type: 'error', text: 'Não foi possível enviar o interesse agora.' }),
    });
  }

  private loadSimilar(property: Property): void {
    this.propertyService.listPublicProperties({ bairro: property.bairro }).subscribe((response) => {
      this.similar = response.results.filter((item) => item.id !== property.id).slice(0, 3);
    });
  }
}
