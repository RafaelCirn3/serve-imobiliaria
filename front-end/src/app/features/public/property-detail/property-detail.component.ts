import { SiteContentService } from '@core/services/site-content.service';
import { SiteSectionDirective } from '@shared/components/site-section.directive';
import { PhotoComponent } from '@shared/components/photo.component';
import { CurrencyPipe, Location } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { environment } from '@env/environment';
import { Property, PropertyUnit } from '@core/models/api.models';
import { propertyArea, propertyTypeLabel, parkingLabel } from '@core/models/property-options';
import { LeadService } from '@core/services/lead.service';
import { NotificationService } from '@core/services/notification.service';
import { PropertyService } from '@core/services/property.service';
import { FooterComponent } from '@shared/components/footer.component';
import { HeaderComponent } from '@shared/components/header.component';
import { LoadingComponent } from '@shared/components/loading.component';
import { PropertyCardComponent } from '@shared/components/property-card.component';
import { PropertyMapComponent } from '@shared/components/property-map.component';

@Component({
  selector: 'app-property-detail',
  standalone: true,
  imports: [SiteSectionDirective, PhotoComponent, CurrencyPipe, ReactiveFormsModule, HeaderComponent, FooterComponent, LoadingComponent, PropertyCardComponent, PropertyMapComponent],
  template: `
    <div class="page-shell">
      <app-header />
      @if (loading) {
        <app-loading />
      } @else if (property) {
        <main class="container detail" data-site-page="detail">
          <button class="back-button" type="button" (click)="goBack()">{{site.text('detail','back_label')}}</button>
          <section class="gallery" appSiteSection="detail.gallery">
            <div class="gallery-stage" tabindex="0" role="group" aria-label="Galeria do imóvel. Use as setas ou deslize para navegar."
              (keydown.arrowleft)="movePhoto(-1); $event.preventDefault()" (keydown.arrowright)="movePhoto(1); $event.preventDefault()"
              (pointerdown)="startSwipe($event)" (pointerup)="finishSwipe($event)" (pointercancel)="cancelSwipe()">
              <app-photo class="main-image" [src]="mainImage" [alt]="property.titulo" [eager]="true" [natural]="true" fit="contain" />
              @if (property.imagens.length > 1) {
                <button class="gallery-arrow previous" type="button" aria-label="Foto anterior" (click)="movePhoto(-1)">&lt;</button>
                <button class="gallery-arrow next" type="button" aria-label="Próxima foto" (click)="movePhoto(1)">&gt;</button>
                <span class="gallery-counter" aria-live="polite">{{ activePhotoIndex + 1 }} / {{ property.imagens.length }}</span>
              }
            </div>
            <div class="thumbs">
              @for (image of property.imagens; track image.id) {
                <button type="button" [class.active]="mainImage === image.imagem" (click)="mainImage = image.imagem"><app-photo [src]="image.imagem" [alt]="image.legenda || property.titulo" /></button>
              }
            </div>
          </section>

          <section class="content">
            <div appSiteSection="detail.description">
              <span class="eyebrow">{{ property.bairro }} · {{ property.cidade }}</span>
              <h1>{{ property.titulo }}</h1>
              <strong class="price">@if (property.agrupado) { <span>A partir de: </span> }{{ numberValue(property.valor_exibicao ?? property.valor) | currency:'BRL':'symbol':'1.0-0':'pt-BR' }}</strong>
              <div class="features">
                <span>{{ typeLabel(property.tipo) }}</span>
                @if (property.torre) { <span>Torre {{ property.torre }}</span> }
                @if (property.situacao_obra === 'em_construcao') { <span>Em construção</span> }
                @if (property.previsao_entrega) { <span>Entrega prevista: {{ property.previsao_entrega.slice(5) }}/{{ property.previsao_entrega.slice(0,4) }}</span> }
                @if (property.quartos > 0) { <span>{{ property.quartos }} quartos</span> }
                @if (property.suites > 0) { <span>{{ property.suites }} suítes</span> }
                @if (property.banheiros > 0) { <span>{{ property.banheiros }} banheiros</span> }
                @if (property.vagas > 0 || property.vagas_rotativas || property.vagas_max) { <span>{{ parkingLabel(property) }}</span> }
                @if (hasArea) { <span>{{ area.label }}: {{ area.value }} m²</span> }
              </div>
              <p class="description">{{ property.descricao }}</p>
              @if (property.agrupado) {
                <section class="unit-options" aria-label="Unidades disponíveis">
                  <h2>Opções disponíveis</h2>
                  <p class="muted">O valor “a partir de” é arredondado para baixo. Confira os valores totais.</p>
                  @if (unitsError) {
                    <p role="status">Não foi possível carregar as unidades. Consulte nossa equipe.</p>
                  } @else if (unitsLoading) {
                    <p role="status">Carregando unidades…</p>
                  } @else {
                    <div class="unit-table-scroll"><table>
                      <thead><tr><th>Torre</th><th>Tipologia</th><th>Área</th><th>Vagas</th><th>Valor total</th></tr></thead>
                      <tbody>@for (unit of units; track $index) {
                        <tr><td data-label="Torre">{{ unit.torre || '—' }}</td><td data-label="Tipologia">@if (unit.quartos) { {{ unit.quartos }} quartos } @else { {{ typeLabel(unit.tipo) }} } @if (unit.suites) { ({{ unit.suites }} suítes) }</td><td data-label="Área">{{ unit.area_privativa || unit.area_total || unit.area_informada }} m²</td><td data-label="Vagas">{{ unit.vagas || '—' }}</td><td data-label="Valor total">{{ numberValue(unit.valor) | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</td></tr>
                      }</tbody>
                    </table></div>
                  }
                </section>
              }
              @if (property.latitude != null && property.longitude != null) {
                <h2>Localização {{ property.localizacao_exata ? 'confirmada' : 'aproximada' }}</h2>
                <app-property-map [properties]="[property]" />
              }
            </div>
          </section>

            <aside class="lead-card card" appSiteSection="detail.interest">
              <h2>{{site.text('detail','interest_title')}}</h2>
              <form [formGroup]="leadForm" (ngSubmit)="sendLead()">
                <input formControlName="nome" placeholder="Nome">
                <input formControlName="email" placeholder="Email">
                <input formControlName="telefone" placeholder="Telefone">
                <textarea formControlName="mensagem" placeholder="Mensagem"></textarea>
                <button class="btn btn-primary" type="submit" [disabled]="leadForm.invalid">{{site.text('detail','interest_button')}}</button>
              </form>
              <a class="btn btn-secondary whatsapp" [href]="whatsappLink" target="_blank" rel="noopener noreferrer" aria-label="Conversar pelo WhatsApp" title="Conversar pelo WhatsApp"><svg aria-hidden="true" width="24" height="24" viewBox="0 0 32 32" fill="currentColor"><path d="M16 .8A15.1 15.1 0 0 0 3.04 23.7L.9 31l7.5-2A15.2 15.2 0 1 0 16 .8Zm0 27.6a12.4 12.4 0 0 1-6.3-1.7l-.45-.27-4.45 1.17 1.2-4.34-.3-.47a12.45 12.45 0 1 1 10.3 5.61Zm6.82-9.27c-.37-.19-2.21-1.1-2.55-1.22-.34-.12-.59-.19-.83.19-.25.37-.96 1.22-1.18 1.46-.22.25-.43.28-.8.1-.37-.19-1.57-.58-2.99-1.85-1.1-.99-1.85-2.21-2.07-2.58-.22-.37-.02-.57.16-.75.17-.17.37-.43.56-.65.19-.22.25-.37.37-.62.12-.25.06-.46-.03-.65-.09-.19-.83-2.01-1.14-2.76-.3-.72-.6-.62-.83-.63h-.7c-.25 0-.65.09-.99.46-.34.37-1.3 1.27-1.3 3.1s1.33 3.6 1.51 3.84c.19.25 2.6 3.97 6.3 5.57.88.38 1.57.61 2.11.78.89.28 1.7.24 2.34.15.71-.11 2.21-.9 2.52-1.77.31-.87.31-1.61.22-1.77-.09-.15-.34-.25-.71-.43Z"/></svg></a>
            </aside>

          @if (similar.length) {
            <section class="section" appSiteSection="detail.similar">
              <h2>{{site.text('detail','similar_title')}}</h2>
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
    .detail[data-site-page] {
      position: relative;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 340px;
      grid-template-areas: 'gallery interest' 'content interest' 'similar similar';
      align-items: start;
      gap: 28px 32px;
      padding: 28px 0 0;
    }

    .back-button {
      position: absolute;
      top: 8px;
      left: -32px;
      z-index: 5;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 42px;
      border: 1px solid rgba(255, 255, 255, 0.38);
      border-radius: 999px;
      background: rgba(17, 20, 23, 0.88);
      backdrop-filter: blur(10px);
      color: #e6e8eb;
      font-weight: 900;
      padding: 0 16px;
      margin: 0;
      transition: background 0.18s ease, transform 0.18s ease;
    }

    .back-button:hover {
      background: rgba(255, 255, 255, 0.12);
      transform: translateX(-2px);
    }

    .gallery {
      grid-area: gallery;
      min-width: 0;
      display: grid;
      gap: 12px;
      animation: fadeUp 0.45s ease both;
    }

    .gallery-stage { position: relative; display: grid; width: fit-content; max-width: 100%; justify-self: center; border-radius: 8px; overflow: hidden; touch-action: pan-y pinch-zoom; user-select: none; }
    .gallery-arrow { position: absolute; top: 0; bottom: 0; width: 64px; max-width: 18%; min-width: 44px; border: 0; border-radius: 0; color: #fff; display: grid; place-items: center; font: 400 34px/1 Arial, sans-serif; text-shadow: 0 1px 5px #000b; z-index: 2; transition: background .2s; }
    .gallery-arrow.previous { left: 0; background: linear-gradient(90deg,#0004,transparent); }
    .gallery-arrow.next { right: 0; background: linear-gradient(270deg,#0004,transparent); }
    .gallery-arrow:hover { background: #0003; }
    .gallery-arrow:focus-visible { outline: 2px solid #fff; outline-offset: -5px; }
    .gallery-counter { position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%); background: #0007; border-radius: 16px; color: #fff; padding: 5px 12px; font-size: 12px; pointer-events: none; }
    .main-image {
      width: fit-content;
      max-width: 100%;
      height: auto;
      justify-self: center;
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
      border-color: #ffffff;
      opacity: 1;
      transform: translateY(-1px);
    }

    .thumbs app-photo {
      width: 120px;
      height: 82px;
      object-fit: cover;
    }

    .content {
      grid-area: content;
      min-width: 0;
      animation: fadeUp 0.5s ease both;
      animation-delay: 0.08s;
    }

    h1 {
      margin: 10px 0 14px;
      font-size: clamp(2rem, 5vw, 4rem);
      line-height: 1.04;
    }

    .price {
      color: #e6e8eb;
      font-size: 2rem;
    }

    .features {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 22px 0;
    }

    .price span { font-size: .7em; }
    .unit-table-scroll { overflow-x: auto; }
    .unit-options table { width: 100%; min-width: 0; border-collapse: collapse; }
    .unit-options th, .unit-options td { padding: 12px 8px; text-align: left; border-bottom: 1px solid #30363d; }
    .unit-options th:last-child, .unit-options td:last-child { text-align: right; white-space: nowrap; }

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
      grid-area: interest;
      min-width: 0;
      align-self: start;
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

    .detail > .section { grid-area: similar; min-width: 0; }

    @media (max-width: 1280px) {
      .back-button { left: 8px; }
    }

    @media (max-width: 900px) {
      .similar-grid {
        grid-template-columns: 1fr;
      }

      .lead-card {
        position: static;
      }

      .detail[data-site-page] {
        grid-template-columns: minmax(0, 1fr);
        grid-template-areas: 'gallery' 'content' 'interest' 'similar';
        padding-top: 22px;
      }

      .thumbs {
        padding-bottom: 4px;
        scroll-snap-type: x proximity;
      }

      .thumbs button {
        scroll-snap-align: start;
      }
    }

    @media (max-width: 600px) {
      .unit-options table, .unit-options tbody { display: block; }
      .unit-options thead { display: none; }
      .unit-options tr { display: grid; grid-template-columns: 1fr 1fr; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 12px; padding: 8px; }
      .unit-options td { border: 0; }
      .unit-options td::before { content: attr(data-label); display: block; font-size: .75rem; color: #aaa; margin-bottom: 5px; }
      .unit-options td:last-child { grid-column: 1 / -1; text-align: left; }
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
 readonly site=inject(SiteContentService);
  readonly typeLabel = propertyTypeLabel;
  readonly parkingLabel = parkingLabel;

  get hasArea() { return Number(this.area.value) > 0; }

  get area() {
    return this.property ? propertyArea(this.property) : { value: null, label: 'Área' };
  }
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  private readonly propertyService = inject(PropertyService);
  private readonly leadService = inject(LeadService);
  private readonly notification = inject(NotificationService);
  private readonly location = inject(Location);

  property: Property | null = null;
  units: PropertyUnit[] = [];
  unitsLoading = false;
  unitsError = false;
  similar: Property[] = [];
  mainImage = '';
  private swipeStart: { x: number; y: number; pointerId: number } | null = null;
  get activePhotoIndex(): number { return Math.max(0, this.property?.imagens.findIndex(image => image.imagem === this.mainImage) ?? 0); }
  movePhoto(direction: number): void {
    const images = this.property?.imagens;
    if (!images || images.length < 2) return;
    this.mainImage = images[(this.activePhotoIndex + direction + images.length) % images.length].imagem;
  }
  startSwipe(event: PointerEvent): void {
    if (!event.isPrimary || event.button !== 0 || (event.target as Element).closest('button')) return;
    this.swipeStart = { x: event.clientX, y: event.clientY, pointerId: event.pointerId };
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  }
  finishSwipe(event: PointerEvent): void {
    const start = this.swipeStart;
    this.swipeStart = null;
    if (!start || start.pointerId !== event.pointerId) return;
    const element = event.currentTarget as HTMLElement;
    if (element.hasPointerCapture(event.pointerId)) element.releasePointerCapture(event.pointerId);
    const dx = event.clientX - start.x, dy = event.clientY - start.y;
    if (Math.abs(dx) >= 40 && Math.abs(dx) > Math.abs(dy) * 1.25) this.movePhoto(dx < 0 ? 1 : -1);
  }
  cancelSwipe(): void { this.swipeStart = null; }
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
        if (property.agrupado) {
          this.unitsLoading = true;
          this.propertyService.getUnits(property.slug).subscribe({
            next: (units) => { this.units = units; this.unitsLoading = false; },
            error: () => { this.unitsError = true; this.unitsLoading = false; },
          });
        }
        this.mainImage = property.imagens?.find(image=>image.imagem_capa)?.imagem || property.imagens?.[0]?.imagem || '';
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
    return `${this.site.whatsapp()}?text=${text}`;
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


