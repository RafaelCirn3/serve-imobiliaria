import { Component, OnInit, HostListener, inject } from '@angular/core';
import { Banner, Property, Region, HomeContent, PropertyCarousel, SectionImage } from '@core/models/api.models';
import { SectionImageService } from '@core/services/section-image.service';
import { PropertyCarouselService } from '@core/services/property-carousel.service';
import { HomeContentService } from '@core/services/home-content.service';
import { BannerService } from '@core/services/banner.service';
import { PropertyService } from '@core/services/property.service';
import { RegionService } from '@core/services/region.service';
import { EmptyStateComponent } from '@shared/components/empty-state.component';
import { FooterComponent } from '@shared/components/footer.component';
import { HeaderComponent } from '@shared/components/header.component';
import { LoadingComponent } from '@shared/components/loading.component';
import { PropertyCardComponent } from '@shared/components/property-card.component';
import { SearchBarComponent } from '@shared/components/search-bar.component';
import { SaleDialogService } from '@core/services/sale-dialog.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [HeaderComponent, FooterComponent, SearchBarComponent, PropertyCardComponent, LoadingComponent, EmptyStateComponent],
  template: `
    <div class="page-shell">
      <app-header />
      <section class="hero">
        @for (banner of banners; track banner.id; let i = $index) {
          <div class="hero-slide" [class.visible]="i === heroIndex" [style.background-image]="'url(' + banner.imagem + ')'"></div>
        }
        <div class="container hero-content">
          @if (banners.length && banners[heroIndex]; as activeBanner) {
            <h1>{{ activeBanner.titulo || content.hero_title }}</h1>
            <p>{{ activeBanner.subtitulo || content.hero_subtitle }}</p>
            @if (activeBanner.botao_link && activeBanner.botao_texto) {
              <a class="btn btn-primary hero-cta" [href]="activeBanner.botao_link">{{ activeBanner.botao_texto }}</a>
            }
          } @else {
            <h1>{{ content.hero_title }}</h1>
            <p>{{ content.hero_subtitle }}</p>
          }
          @if (totalPublicProperties !== null) {
            <p aria-live="polite">{{ totalPublicProperties }} {{ totalPublicProperties === 1 ? 'imóvel disponível' : 'imóveis disponíveis' }} no catálogo.</p>
          }
        </div>
        @if (banners.length > 1) {
          <div class="hero-controls">
            <button type="button" aria-label="Slide anterior" (click)="moveHero(-1)">‹</button>
            <span aria-live="polite">{{ heroIndex + 1 }} / {{ banners.length }}</span>
            <button type="button" aria-label="Próximo slide" (click)="moveHero(1)">›</button>
          </div>
        }
        <div class="container hero-search-wrap">
          <app-search-bar variant="hero" />
        </div>
      </section>

      <section class="section">
        <div class="container">
          <span class="eyebrow">{{ content.featured_label }}</span>
          <h2 class="section-title">{{ content.featured_title }}</h2>
          @if (loadingFeatured) {
            <app-loading />
          } @else if (featured.length) {
            <div class="carousel-shell" (touchstart)="touchStart($event)" (touchend)="touchEnd($event)">
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

      @for (carousel of extraCarousels; track carousel.id) {
        @if (carousel.properties?.length) {
          <section class="section">
            <div class="container">
              <h2 class="section-title">{{ carousel.titulo }}</h2>
              @if (carousel.subtitulo) { <p class="muted">{{ carousel.subtitulo }}</p> }
              <div class="carousel-shell">
                <div class="carousel-head">
                  <span class="muted">{{ carousel.properties?.length }} imóveis</span>
                  <div class="carousel-actions">
                    <button class="carousel-btn" type="button" [attr.aria-label]="'Voltar imóveis de ' + carousel.titulo" (click)="moveExtra(carousel,-1)">‹</button>
                    <button class="carousel-btn" type="button" [attr.aria-label]="'Avançar imóveis de ' + carousel.titulo" (click)="moveExtra(carousel,1)">›</button>
                  </div>
                </div>
                <div class="carousel-viewport">
                  <div class="carousel-track" [style.transform]="extraTransform(carousel)">
                    @for (property of carousel.properties ?? []; track property.id) {
                      <div class="carousel-slide"><app-property-card [property]="property" /></div>
                    }
                  </div>
                </div>
              </div>
            </div>
          </section>
        }
      }
      <section class="section regions">
        <div class="container">
          <span class="eyebrow">{{ content.regions_label }}</span>
          <h2 class="section-title">{{ content.regions_title }}</h2>
          @if (tourismImages.length) {
            <div class="editorial-gallery">
              <button type="button" aria-label="Imagem turística anterior" (click)="moveGallery('tourism',-1)">‹</button>
              <figure><img [src]="tourismImages[tourismIndex].image" [alt]="tourismImages[tourismIndex].caption || 'Ponto turístico'">
                @if (tourismImages[tourismIndex].caption) {<figcaption>{{ tourismImages[tourismIndex].caption }}</figcaption>}
              </figure>
              <button type="button" aria-label="Próxima imagem turística" (click)="moveGallery('tourism',1)">›</button>
            </div>
          } @else {
            <div class="region-grid">
              @for (region of regions; track region.id) {
                <article class="region-card card">
                  <img [src]="regionImage(region)" [alt]="region.nome">
                  <div><h3>{{ region.nome }}</h3><p>{{ region.descricao || 'Região estratégica para morar ou investir em ' + region.cidade + '.' }}</p></div>
                </article>
              }
            </div>
          }
        </div>
      </section>

      <section class="section invest">
        <div class="container split">
          <div>
            <span class="eyebrow">{{ content.investment_label }}</span>
            <h2 class="section-title">{{ content.investment_title }}</h2>
          </div>
          <div>
            @if (investmentImages.length) {
              <div class="editorial-gallery">
                <button type="button" aria-label="Imagem anterior da orla" (click)="moveGallery('investment',-1)">‹</button>
                <figure><img [src]="investmentImages[investmentIndex].image" [alt]="investmentImages[investmentIndex].caption || 'Orla de João Pessoa'">
                  @if (investmentImages[investmentIndex].caption) {<figcaption>{{ investmentImages[investmentIndex].caption }}</figcaption>}
                </figure>
                <button type="button" aria-label="Próxima imagem da orla" (click)="moveGallery('investment',1)">›</button>
              </div>
            }
            <div class="card text-card">
              <p>{{ content.investment_body }}</p>
              <p>{{ content.investment_extra }}</p>
            </div>
          </div>
        </div>
      </section>

      <section id="proprietarios" class="section owner">
        <div class="container owner-box">
          <div>
            <span class="eyebrow">{{ content.owner_label }}</span>
            <h2>{{ content.owner_title }}</h2>
            <p>{{ content.owner_body }}</p>
          </div>
          <button type="button" class="btn btn-primary" (click)="saleDialog.open()">{{ content.owner_button }}</button>
        </div>
      </section>
      <app-footer />
    </div>
  `,
  styles: [`
    .hero {
      position: relative;
      isolation: isolate;
      min-height: min(760px, 88vh);
      display: grid;
      align-items: center;
      padding: 110px 0 48px;
      background:
        linear-gradient(180deg, rgba(17, 20, 23, 0.12), rgba(17, 20, 23, 0.24) 58%, #0d1013 100%),
        linear-gradient(90deg, rgba(17, 20, 23, 0.54), rgba(17, 20, 23, 0.14) 40%, rgba(17, 20, 23, 0) 68%),
        url('/assets/hero-joao-pessoa.jpg') center/cover;
    }

    .hero-slide {
      position: absolute; inset: 0; z-index: 0;
      background-size: cover; background-position: center;
      opacity: 0; transition: opacity .65s ease; pointer-events: none;
    }
    .hero-slide.visible { opacity: 1; }
    .hero-slide::after { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(10,20,26,.68), rgba(10,20,26,.12) 75%), linear-gradient(0deg, rgba(10,20,26,.75), transparent 65%); }
    .hero > .container, .hero-controls { position: relative; z-index: 1; }
    .hero-cta { width: fit-content; }
    .hero-controls { display:flex; justify-content:center; align-items:center; gap:18px; z-index:2; }
    .hero-controls button { border:1px solid #aaa; background:#171c20c9; color:white; border-radius:50%; width:40px; height:40px; font-size:26px; }
    .hero-content {
      display: grid;
      gap: 16px;
      width: min(390px, calc(100% - 48px));
      max-width: 390px;
      margin-left: clamp(24px, 3.5vw, 60px);
      margin-right: auto;
      text-shadow: 0 2px 18px rgba(0, 0, 0, 0.34);
    }

    h1 {
      max-width: 390px;
      margin: 0;
      font-size: clamp(2rem, 3.2vw, 3.6rem);
      line-height: 1.12;
    }

    .hero p {
      max-width: 560px;
      margin: 0;
      color: rgba(245, 245, 245, 0.78);
      font-size: 1rem;
      line-height: 1.65;
    }


    .hero-search-wrap {
      margin-top: 22px;
      margin-bottom: 28px;
    }

    .hero .eyebrow {
      color: rgba(245, 245, 245, 0.76);
    }

    .editorial-gallery { display:flex; align-items:center; gap:12px; margin:24px 0; min-width:0; }
    .editorial-gallery figure { flex:1; min-width:0; margin:0; position:relative; }
    .editorial-gallery img { display:block; width:100%; aspect-ratio:16/9; object-fit:cover; border-radius:9px; }
    .editorial-gallery figcaption { position:absolute; bottom:0; left:0; right:0; padding:14px; background:linear-gradient(transparent,rgba(0,0,0,.85)); color:white; }
    .editorial-gallery button { flex:0 0 36px; height:42px; background:#30363d; border:1px solid #777; color:#fff; border-radius:8px; font-size:24px; }
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
      border: 1px solid rgba(255, 255, 255, 0.4);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.07);
      color: #e6e8eb;
      font-size: 1.9rem;
      line-height: 1;
      padding: 3px 0 0;
      transition: background 0.18s ease, transform 0.18s ease;
    }

    .carousel-btn:hover {
      background: rgba(255, 255, 255, 0.14);
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
      flex: 0 0 25%;
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
      background: #ffffff;
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
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.025));
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
        min-height: 680px;
        padding: 116px 0 42px;
        background-position: 34% center;
      }

      .hero-content {
        width: calc(100% - 32px);
        max-width: 700px;
        margin-left: 16px;
        margin-right: 16px;
      }

      .hero-search-wrap {
        margin-top: 18px;
      }
      .hero-content { background: rgba(7, 22, 31, .28); border-radius: 8px; padding: 12px; }
    }

    @media (min-width: 901px) and (max-width: 1120px) {
      .carousel-slide {
        flex-basis: 50%;
      }
    }
  `],
})
export class HomeComponent implements OnInit {
  readonly saleDialog = inject(SaleDialogService);
  private readonly propertyService = inject(PropertyService);
  private readonly regionService = inject(RegionService);
  private readonly bannerService = inject(BannerService);
  private readonly homeService = inject(HomeContentService);
  private readonly extraService = inject(PropertyCarouselService);
  private readonly galleryService = inject(SectionImageService);

  content: HomeContent = {hero_title:'O Melhor de João Pessoa para o seu novo capítulo.',hero_subtitle:'Encontre os melhores imóveis e investimentos, e realize-se!',featured_label:'Curadoria SERVE',featured_title:'Imóveis em destaque',regions_label:'Localização importa',regions_title:'Regiões mais procuradas',investment_label:'Investir em João Pessoa',investment_title:'Orla, qualidade de vida e valorização em uma capital em movimento.',investment_body:'João Pessoa combina bairros consolidados, novas frentes de desenvolvimento e uma relação rara entre praia, serviços e tranquilidade urbana.',investment_extra:'A SERVE organiza essa leitura para quem quer decidir com segurança: localização, liquidez, padrão do imóvel e momento de mercado.',owner_label:'Para proprietários',owner_title:'Anuncie com apresentação premium e gestão direta.',owner_body:'Seu imóvel merece imagens fortes, texto objetivo e uma jornada de contato sem atrito.',owner_button:'Falar com a SERVE'};
  heroIndex = 0;
  tourismImages: SectionImage[] = [];
  investmentImages: SectionImage[] = [];
  tourismIndex = 0;
  investmentIndex = 0;
  private touchX = 0;
  extraCarousels: PropertyCarousel[] = [];
  extraIndexes: Record<number,number> = {};
  featured: Property[] = [];
  totalPublicProperties: number | null = null;
  regions: Region[] = [];
  banners: Banner[] = [];
  loadingFeatured = true;
  featuredIndex = 0;
  fallbackRegionImage = 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1000&q=80';

  get visibleFeaturedCount(): number {
    if (typeof window === 'undefined') {
      return 4;
    }
    if (window.innerWidth <= 900) {
      return 1;
    }
    if (window.innerWidth <= 1120) {
      return 2;
    }
    return 4;
  }

  get carouselTransform(): string {
    return `translateX(-${this.featuredIndex * (100 / this.visibleFeaturedCount)}%)`;
  }

  get carouselDots(): number[] {
    return Array.from({ length: this.maxFeaturedIndex + 1 }, (_, index) => index);
  }

  ngOnInit(): void {
    this.homeService.load().subscribe({next: content => this.content = content});
    this.galleryService.list().subscribe({next: response => {this.tourismImages = response.results.filter(i => i.section === 'tourism'); this.investmentImages = response.results.filter(i => i.section === 'investment');}});
    this.extraService.list().subscribe({next: response => this.extraCarousels = response.results});
    this.propertyService.listPublicProperties().subscribe({
      next: (response) => (this.totalPublicProperties = response.count),
      error: () => (this.totalPublicProperties = null),
    });
    this.propertyService.getFeaturedProperties().subscribe({
      next: (response) => {
        this.featured = response.results;
        this.featuredIndex = 0;
        this.loadingFeatured = false;
      },
      error: () => {
        this.loadingFeatured = false;
      },
    });
    this.regionService.listRegions().subscribe((response) => (this.regions = response.results.slice(0, 6)));
    this.bannerService.listBanners().subscribe((response) => (this.banners = response.results.filter(b => b.ativo).sort((a,b) => a.ordem - b.ordem)));
  }

  regionImage(region: Region): string {
    return typeof region.imagem === 'string' && region.imagem ? region.imagem : this.fallbackRegionImage;
  }

  extraTransform(carousel: PropertyCarousel): string {
    return `translateX(-${(this.extraIndexes[carousel.id] || 0) * (100 / this.visibleFeaturedCount)}%)`;
  }

  moveExtra(carousel: PropertyCarousel, delta: number): void {
    const count = carousel.properties?.length || 0;
    const last = Math.max(count - this.visibleFeaturedCount, 0);
    const current = this.extraIndexes[carousel.id] || 0;
    this.extraIndexes[carousel.id] = delta > 0 ? (current >= last ? 0 : current + 1) : (current <= 0 ? last : current - 1);
  }

  moveGallery(section: 'tourism' | 'investment', delta: number): void {
    const images = section === 'tourism' ? this.tourismImages : this.investmentImages;
    if (!images.length) return;
    if (section === 'tourism') this.tourismIndex = (this.tourismIndex + delta + images.length) % images.length;
    else this.investmentIndex = (this.investmentIndex + delta + images.length) % images.length;
  }

  moveHero(delta: number): void {
    if (this.banners.length) this.heroIndex = (this.heroIndex + delta + this.banners.length) % this.banners.length;
  }

  touchStart(event: TouchEvent): void { this.touchX = event.changedTouches[0].screenX; }
  touchEnd(event: TouchEvent): void {
    const movement = event.changedTouches[0].screenX - this.touchX;
    if (Math.abs(movement) > 45) movement < 0 ? this.nextFeatured() : this.previousFeatured();
  }

  @HostListener('window:resize')
  onResize(): void { this.featuredIndex = Math.min(this.featuredIndex, this.maxFeaturedIndex); }

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
