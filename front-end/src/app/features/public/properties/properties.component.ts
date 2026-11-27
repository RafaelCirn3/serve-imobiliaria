import { SiteContentService } from '@core/services/site-content.service';
import { SiteSectionDirective } from '@shared/components/site-section.directive';
import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, forkJoin, of, switchMap } from 'rxjs';
import { ActivatedRoute, Router } from '@angular/router';
import { Property, PropertyFilters } from '@core/models/api.models';
import { PropertyService } from '@core/services/property.service';
import { EmptyStateComponent } from '@shared/components/empty-state.component';
import { FilterSidebarComponent } from '@shared/components/filter-sidebar.component';
import { FooterComponent } from '@shared/components/footer.component';
import { HeaderComponent } from '@shared/components/header.component';
import { LoadingComponent } from '@shared/components/loading.component';
import { PropertyCardComponent } from '@shared/components/property-card.component';
import { PropertyMapComponent } from '@shared/components/property-map.component';
import { MapResponse } from '@core/models/api.models';

@Component({
  selector: 'app-properties',
  standalone: true,
  imports: [SiteSectionDirective, HeaderComponent, FooterComponent, FilterSidebarComponent, PropertyCardComponent, LoadingComponent, EmptyStateComponent, PropertyMapComponent],
  template: `
    <div class="page-shell">
      <app-header />
      <main class="section container catalog-page" data-site-page="properties">
        <div class="catalog-intro" appSiteSection="properties.intro"><span class="eyebrow">{{site.text('properties','label')}}</span>
        <h1 class="section-title">{{site.text('properties','title').replace('{cidade}',filters.cidade || site.text('properties','default_cities'))}}</h1></div>
        <div class="layout" appSiteSection="properties.catalog">
          <aside class="filters-column" aria-label="Filtros de imóveis">
            <app-filter-sidebar [initialFilters]="filters" (filtersChanged)="applyFilters($event)" />
          </aside>
          <section class="results-column">
            <div class="catalog-toolbar">
            <div class="view-switch" aria-label="Visualização dos imóveis">
              <button type="button" class="btn btn-secondary" [attr.aria-pressed]="view === 'lista'" (click)="changeView('lista')">{{site.text('properties','list_label')}}</button>
              <button type="button" class="btn btn-secondary" [attr.aria-pressed]="view === 'mapa'" (click)="changeView('mapa')">{{site.text('properties','map_label')}}</button>
            </div>
            @if (!loading && !error) {
              <div class="result-meta">
                <span aria-live="polite">{{ total }} resultado(s)</span>
                @if (view === 'lista' && (hasNext || page > 1)) {
                  <nav aria-label="Páginas de imóveis">
                    <button class="btn btn-secondary" type="button" (click)="loadPage(page - 1)" [disabled]="page <= 1">Anterior</button>
                    <button class="btn btn-secondary" type="button" (click)="loadPage(page + 1)" [disabled]="!hasNext">Próxima</button>
                  </nav>
                }
              </div>
            }
            </div>
            @if (loading) {
              <app-loading />
            } @else if (error) {
              <p role="alert">{{ error }}</p><button type="button" class="btn btn-secondary" (click)="retry()">Tentar novamente</button>
            } @else if (view === 'mapa' && mapData) {
              <p>{{ mapData.count }} resultado(s) · {{ mapData.geolocalizados }} com localização · {{ mapData.sem_coordenadas }} disponíveis apenas na lista.</p>
              @if (mapData.truncado) { <p role="status">Exibindo até {{ mapData.limite }} marcadores. Refine cidade, bairro ou rua para ver todos.</p> }
              @if (mapError) { <p role="alert">{{ mapError }}</p> }
              @else if (mapData.results.length) { <app-property-map [properties]="mapData.results" /> }
              @else { <p>Nenhum imóvel com coordenadas neste recorte. Consulte a lista.</p> }
            } @else if (mapError && view === 'mapa') {
              <p role="alert">{{ mapError }}</p><button class="btn btn-secondary" type="button" (click)="changeView('lista')">Ver lista</button>
            } @else if (properties.length) {
              <div class="property-grid">
                @for (property of properties; track property.id) {
                  <app-property-card [property]="property" />
                }
              </div>
            } @else {
              <app-empty-state />
            }
          </section>
        </div>
      </main>
      <app-footer />
    </div>
  `,
  styles: [`
    .catalog-page { width: min(1560px, calc(100% - 64px)); padding-top: 36px; }
    .catalog-intro .section-title { font-size: clamp(1.8rem, 2.7vw, 2.75rem); max-width: 1100px; margin: 8px 0 0; }
    .catalog-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 20px; }
    .view-switch { display: flex; gap: 8px; }
    .view-switch button[aria-pressed="true"] { border-color: white; background: #ffffff20; }

    .layout {
      display: grid;
      grid-template-columns: 248px minmax(0, 1fr);
      gap: 24px;
      align-items: start;
      margin-top: 24px;
    }

    .filters-column,
    .results-column {
      min-width: 0;
    }
    .filters-column { position: sticky; top: 100px; max-height: calc(100dvh - 120px); overflow-y: auto; scrollbar-width: thin; }

    .property-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 24px 20px;
      align-items: stretch;
    }

    .result-meta {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      color: #b8b8b8;
    }
    .result-meta nav { display: flex; gap: 8px; }

    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    @media (max-width: 1199px) {
      .layout { grid-template-columns: 224px minmax(0, 1fr); gap: 20px; }
      .property-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 899px) {
      .catalog-page { width: calc(100% - 32px); }
      .layout { grid-template-columns: minmax(0, 1fr); }
      .filters-column { position: static; max-height: none; overflow: visible; }
    }
    @media (max-width: 599px) {
      .catalog-page { padding-top: 28px; }
      .property-grid { grid-template-columns: minmax(0, 1fr); gap: 20px; }
      .catalog-toolbar { gap: 12px; }
      .result-meta { font-size: .85rem; }
    }
  `],
})
export class PropertiesComponent implements OnInit {
 readonly site=inject(SiteContentService);
  private readonly propertyService = inject(PropertyService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  properties: Property[] = [];
  filters: PropertyFilters = {};
  loading = true;
  total = 0;
  page = 1;
  hasNext = false;
  error = '';
  mapError = '';
  mapData: MapResponse | null = null;
  get view(): 'lista' | 'mapa' { return this.filters.visualizacao === 'mapa' ? 'mapa' : 'lista'; }

  ngOnInit(): void {
    this.route.queryParams.pipe(switchMap((params) => {
      this.filters = { ...params };
      this.loading = true; this.error = ''; this.mapError = ''; this.mapData = null;
      this.page = Number(this.filters.page || 1);
      const request = this.filters.search
        ? this.propertyService.searchProperties(String(this.filters.search), this.filters)
        : this.propertyService.listPublicProperties(this.filters);
      const list = this.view === 'mapa' ? of(null) : request.pipe(catchError(() => { this.error = 'Não foi possível carregar os imóveis. Revise os filtros ou tente novamente.'; return of(null); }));
      const map = this.view === 'mapa' ? this.propertyService.mapProperties(this.filters).pipe(catchError(() => { this.mapError = 'Não foi possível carregar as localizações. Consulte a lista.'; return of(null); })) : of(null);
      return forkJoin({ list, map });
    }), takeUntilDestroyed(this.destroyRef)).subscribe(({ list: response, map }) => {
      this.mapData = map;
      this.properties = response?.results || [];
      this.total = response?.count || map?.count || 0;
      this.hasNext = Boolean(response?.next); this.loading = false;
    });
  }

  applyFilters(filters: PropertyFilters): void {
    this.router.navigate(['/imoveis'], { queryParams: { ...filters, visualizacao: this.view, page: 1 } });
  }

  loadPage(page: number): void {
    this.router.navigate(['/imoveis'], { queryParams: { ...this.filters, page } });
  }

  retry(): void { window.location.reload(); }
  changeView(visualizacao: 'lista' | 'mapa'): void {
    this.router.navigate(['/imoveis'], { queryParams: { ...this.filters, visualizacao, page: 1 } });
  }
}


