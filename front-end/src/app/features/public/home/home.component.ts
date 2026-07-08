import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Banner, Property, Region } from '@core/models/api.models';
import { BannerService } from '@core/services/banner.service';
import { PropertyService } from '@core/services/property.service';
import { RegionService } from '@core/services/region.service';
import { EmptyStateComponent } from '@shared/components/empty-state.component';
import { FooterComponent } from '@shared/components/footer.component';
import { HeaderComponent } from '@shared/components/header.component';
import { LoadingComponent } from '@shared/components/loading.component';
import { PropertyCardComponent } from '@shared/components/property-card.component';
import { SearchBarComponent } from '@shared/components/search-bar.component';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [RouterLink, HeaderComponent, FooterComponent, SearchBarComponent, PropertyCardComponent, LoadingComponent, EmptyStateComponent],
  template: `
    <div class="page-shell">
      <app-header />
      <section class="hero">
        <div class="container hero-content">
          <span class="eyebrow">João Pessoa / PB</span>
          <h1>O melhor de João Pessoa para o seu novo capítulo.</h1>
          <p>Imóveis selecionados com critério, apresentação premium e atendimento direto para comprar, vender ou alugar com clareza.</p>
          <app-search-bar />
        </div>
      </section>

      <section class="section">
        <div class="container">
          <span class="eyebrow">Curadoria SERVE</span>
          <h2 class="section-title">Imóveis em destaque</h2>
          @if (loadingFeatured) {
            <app-loading />
          } @else if (featured.length) {
            <div class="carousel-shell">
              <div class="carousel-head">
                <p class="muted">Arraste no mobile ou use os controles para navegar pela curadoria.</p>
                <div class="carousel-actions">
                  <button class="carousel-btn" type="button" aria-label="Imóveis anteriores" (click)="previousFeatured()">&lsaquo;</button>
                  <button class="carousel-btn" type="button" aria-label="Próximos imóveis" (click)="nextFeatured()">&rsaquo;</button>
                </div>
              </div>
              <div class="carousel-viewport">
                <div class="carousel-track" [style.transform]="carouselTransform">
                  @for (property of featured; track property.id) {
                    <div class="carousel-slide">
                      <app-property-card [property]="property" />
                    </div>
                  }
                </div>
              </div>
              <div class="carousel-dots" aria-label="Navegação dos imóveis em destaque">
                @for (index of carouselDots; track index) {
                  <button type="button" [class.active]="index === featuredIndex" (click)="goToFeatured(index)" [attr.aria-label]="'Ir para grupo ' + (index + 1)"></button>
                }
              </div>
            </div>
          } @else {
            <app-empty-state title="Nenhum destaque publicado" message="Assim que houver imóveis em destaque, eles aparecerão aqui." />
          }
        </div>
      </section>

      <section class="section regions">
        <div class="container">
          <span class="eyebrow">Localização importa</span>
          <h2 class="section-title">Regiões mais procuradas</h2>
          <div class="region-grid">
            @for (region of regions; track region.id) {
              <article class="region-card card">
                <img [src]="regionImage(region)" [alt]="region.nome">
                <div>
                  <h3>{{ region.nome }}</h3>
                  <p>{{ region.descricao || 'Região estratégica para morar ou investir em João Pessoa.' }}</p>
                </div>
              </article>
            }
          </div>
        </div>
      </section>

      <section class="section invest">
        <div class="container split">
          <div>
            <span class="eyebrow">Investir em João Pessoa</span>
            <h2 class="section-title">Orla, qualidade de vida e valorização em uma capital em movimento.</h2>
          </div>
          <div class="card text-card">
            <p>João Pessoa combina bairros consolidados, novas frentes de desenvolvimento e uma relação rara entre praia, serviços e tranquilidade urbana.</p>
            <p>A SERVE organiza essa leitura para quem quer decidir com segurança: localização, liquidez, padrão do imóvel e momento de mercado.</p>
          </div>
        </div>
      </section>

      <section id="proprietarios" class="section owner">
        <div class="container owner-box">
          <div>
            <span class="eyebrow">Para proprietários</span>
            <h2>Anuncie com apresentação premium e gestão direta.</h2>
            <p>Seu imóvel merece imagens fortes, texto objetivo e uma jornada de contato sem atrito.</p>
          </div>
          <a class="btn btn-primary" routerLink="/contato">Falar com a SERVE</a>
        </div>
      </section>
      <app-footer />
    </div>
  `,
  styles: [`
    .hero {
      min-height: 720px;
      display: grid;
      align-items: end;
      padding: 140px 0 80px;
      background:
        linear-gradient(180deg, rgba(17, 20, 23, 0.12), #111417 96%),
        linear-gradient(90deg, rgba(17, 20, 23, 0.92), rgba(17, 20, 23, 0.2)),
        url('https://images.unsplash.com/photo-1516306580123-e6e52b1b7b5f?auto=format&fit=crop&w=1800&q=85') center/cover;
    }

    .hero-content {
      display: grid;
      gap: 22px;
      max-width: 980px;
    }

    h1 {
      max-width: 820px;
      margin: 0;
      font-size: clamp(3rem, 7vw, 6.7rem);
      line-height: 0.95;
      letter-spacing: -0.03em;
    }

    .hero p {
      max-width: 650px;
      color: #d7d7d7;
      font-size: 1.12rem;
      line-height: 1.7;
    }

    .region-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
      margin-top: 28px;
    }

    .carousel-shell {
      margin-top: 28px;
    }

    .carousel-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 14px;
      min-height: 44px;
    }

    .carousel-head p {
      margin: 0;
    }

    .carousel-actions {
      display: flex;
      gap: 8px;
      flex: 0 0 auto;
    }

    .carousel-btn {
      display: inline-grid;
      place-items: center;
      width: 44px;
      height: 44px;
      border: 1px solid rgba(201, 162, 74, 0.45);
      border-radius: 999px;
      background: rgba(201, 162, 74, 0.08);
      color: #d6b765;
      font-size: 1.9rem;
      line-height: 1;
      padding: 3px 0 0;
      transition: background 0.18s ease, transform 0.18s ease;
    }

    .carousel-btn:hover {
      background: rgba(201, 162, 74, 0.18);
      transform: translateY(-1px);
    }

    .carousel-viewport {
      overflow: hidden;
      padding: 4px 0;
    }

    .carousel-track {
      display: flex;
      transition: transform 0.45s cubic-bezier(0.22, 1, 0.36, 1);
      will-change: transform;
    }

    .carousel-slide {
      flex: 0 0 33.333%;
      padding-right: 18px;
      min-width: 0;
    }

    .carousel-dots {
      display: flex;
      justify-content: center;
      gap: 8px;
      margin-top: 16px;
    }

    .carousel-dots button {
      width: 8px;
      height: 8px;
      border: 0;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.26);
      padding: 0;
      transition: width 0.2s ease, background 0.2s ease;
    }

    .carousel-dots button.active {
      width: 26px;
      background: #c9a24a;
    }

    .regions {
      background: #181c20;
    }

    .region-card {
      overflow: hidden;
    }

    .region-card img {
      width: 100%;
      aspect-ratio: 1.55;
      object-fit: cover;
    }

    .region-card div {
      padding: 18px;
    }

    .region-card h3,
    .owner h2 {
      margin: 0 0 10px;
    }

    .region-card p,
    .text-card p,
    .owner p {
      color: #b8b8b8;
      line-height: 1.75;
    }

    .split,
    .owner-box {
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 28px;
      align-items: center;
    }

    .text-card,
    .owner-box {
      padding: 28px;
    }

    .owner-box {
      border: 1px solid rgba(201, 162, 74, 0.28);
      border-radius: 8px;
      background: linear-gradient(135deg, rgba(201, 162, 74, 0.11), rgba(255, 255, 255, 0.025));
    }

    @media (max-width: 900px) {
      .region-grid,
      .split,
      .owner-box {
        grid-template-columns: 1fr;
      }

      .carousel-slide {
        flex-basis: 100%;
        padding-right: 0;
      }

      .carousel-head {
        align-items: flex-start;
        flex-direction: column;
      }

      .hero {
        min-height: 640px;
      }
    }

    @media (min-width: 901px) and (max-width: 1120px) {
      .carousel-slide {
        flex-basis: 50%;
      }
    }
  `],
})
export class HomeComponent implements OnInit {
  private readonly propertyService = inject(PropertyService);
  private readonly regionService = inject(RegionService);
  private readonly bannerService = inject(BannerService);

  featured: Property[] = [];
  regions: Region[] = [];
  banners: Banner[] = [];
  loadingFeatured = true;
  featuredIndex = 0;
  fallbackRegionImage = 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1000&q=80';

  get visibleFeaturedCount(): number {
    if (typeof window === 'undefined') {
      return 3;
    }
    if (window.innerWidth <= 900) {
      return 1;
    }
    if (window.innerWidth <= 1120) {
      return 2;
    }
    return 3;
  }

  get carouselTransform(): string {
    return `translateX(-${this.featuredIndex * (100 / this.visibleFeaturedCount)}%)`;
  }

  get carouselDots(): number[] {
    return Array.from({ length: this.maxFeaturedIndex + 1 }, (_, index) => index);
  }

  ngOnInit(): void {
    this.propertyService.getFeaturedProperties().subscribe({
      next: (response) => {
        this.featured = response.results.slice(0, 6);
        this.featuredIndex = 0;
        this.loadingFeatured = false;
      },
      error: () => {
        this.loadingFeatured = false;
      },
    });
    this.regionService.listRegions().subscribe((response) => (this.regions = response.results.slice(0, 6)));
    this.bannerService.listBanners().subscribe((response) => (this.banners = response.results));
  }

  regionImage(region: Region): string {
    return typeof region.imagem === 'string' && region.imagem ? region.imagem : this.fallbackRegionImage;
  }

  nextFeatured(): void {
    this.featuredIndex = this.featuredIndex >= this.maxFeaturedIndex ? 0 : this.featuredIndex + 1;
  }

  previousFeatured(): void {
    this.featuredIndex = this.featuredIndex <= 0 ? this.maxFeaturedIndex : this.featuredIndex - 1;
  }

  goToFeatured(index: number): void {
    this.featuredIndex = Math.min(index, this.maxFeaturedIndex);
  }

  private get maxFeaturedIndex(): number {
    return Math.max(this.featured.length - this.visibleFeaturedCount, 0);
  }
}
