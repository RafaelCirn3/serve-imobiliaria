import { CurrencyPipe } from '@angular/common';
import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Property } from '@core/models/api.models';

@Component({
  selector: 'app-property-card',
  standalone: true,
  imports: [RouterLink, CurrencyPipe],
  template: `
    <article class="property-card card">
      <a [routerLink]="['/imoveis', property.slug]" class="media">
        <img [src]="coverImage" [alt]="property.titulo">
        @if (property.destaque) {
          <span>Destaque</span>
        }
      </a>
      <div class="content">
        <p class="location">{{ property.bairro }} · {{ property.cidade }}</p>
        <h3><a [routerLink]="['/imoveis', property.slug]">{{ property.titulo }}</a></h3>
        <strong class="price">{{ numericPrice | currency:'BRL':'symbol':'1.0-0':'pt-BR' }}</strong>
        <div class="features">
          <span>{{ property.quartos }} quartos</span>
          <span>{{ property.suites }} suítes</span>
          <span>{{ property.vagas }} vagas</span>
          <span>{{ property.area_privativa || property.area_total || '-' }} m²</span>
        </div>
      </div>
    </article>
  `,
  styles: [`
    :host {
      display: block;
      min-width: 0;
      height: 100%;
    }

    .property-card {
      display: flex;
      flex-direction: column;
      height: 100%;
      min-width: 0;
      overflow: hidden;
      transition: transform 0.18s ease, border-color 0.18s ease;
    }

    .property-card:hover {
      border-color: rgba(255, 255, 255, 0.48);
      transform: translateY(-3px);
    }

    .media {
      position: relative;
      display: block;
      aspect-ratio: 1.38;
      background: #111417;
    }

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.45s cubic-bezier(0.22, 1, 0.36, 1), filter 0.2s ease;
    }

    .property-card:hover img {
      transform: scale(1.045);
      filter: saturate(1.08);
    }

    .media span {
      position: absolute;
      left: 12px;
      top: 12px;
      border-radius: 999px;
      background: #ffffff;
      color: #111417;
      padding: 6px 10px;
      font-size: 0.75rem;
      font-weight: 900;
    }

    .content {
      display: flex;
      flex: 1;
      flex-direction: column;
      min-width: 0;
      padding: 18px;
    }

    .location {
      margin: 0 0 8px;
      color: #ffffff;
      font-size: 0.82rem;
      font-weight: 800;
      text-transform: uppercase;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    h3 {
      margin: 0 0 12px;
      font-size: 1.15rem;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }

    .price {
      display: block;
      color: #e6e8eb;
      font-size: 1.25rem;
      margin-bottom: 14px;
      overflow-wrap: anywhere;
    }

    .features {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: auto;
    }

    .features span {
      border: 1px solid #30363d;
      border-radius: 999px;
      color: #b8b8b8;
      padding: 5px 9px;
      font-size: 0.78rem;
    }
  `],
})
export class PropertyCardComponent {
  @Input({ required: true }) property!: Property;

  get coverImage(): string {
    return this.property.imagens?.find((image) => image.imagem_capa)?.imagem
      || this.property.imagens?.[0]?.imagem
      || 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80';
  }

  get numericPrice(): number {
    return Number(this.property.valor || 0);
  }
}


