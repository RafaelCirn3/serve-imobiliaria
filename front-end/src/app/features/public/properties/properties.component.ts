import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Property, PropertyFilters } from '@core/models/api.models';
import { PropertyService } from '@core/services/property.service';
import { EmptyStateComponent } from '@shared/components/empty-state.component';
import { FilterSidebarComponent } from '@shared/components/filter-sidebar.component';
import { FooterComponent } from '@shared/components/footer.component';
import { HeaderComponent } from '@shared/components/header.component';
import { LoadingComponent } from '@shared/components/loading.component';
import { PropertyCardComponent } from '@shared/components/property-card.component';

@Component({
  selector: 'app-properties',
  standalone: true,
  imports: [HeaderComponent, FooterComponent, FilterSidebarComponent, PropertyCardComponent, LoadingComponent, EmptyStateComponent],
  template: `
    <div class="page-shell">
      <app-header />
      <main class="section container">
        <span class="eyebrow">Portfolio SERVE</span>
        <h1 class="section-title">Imóveis em João Pessoa</h1>
        <div class="layout">
          <aside class="filters-column">
            <app-filter-sidebar [initialFilters]="filters" (filtersChanged)="applyFilters($event)" />
          </aside>
          <section class="results-column">
            @if (loading) {
              <app-loading />
            } @else if (properties.length) {
              <div class="result-meta">
                <span>{{ total }} resultado(s)</span>
                <button class="btn btn-secondary" type="button" (click)="loadPage(page - 1)" [disabled]="page <= 1">Anterior</button>
                <button class="btn btn-secondary" type="button" (click)="loadPage(page + 1)" [disabled]="!hasNext">Próxima</button>
              </div>
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
    main {
      padding-top: 54px;
    }

    .layout {
      display: grid;
      grid-template-columns: minmax(260px, 300px) minmax(0, 1fr);
      gap: 24px;
      align-items: start;
      margin-top: 28px;
    }

    .filters-column,
    .results-column {
      min-width: 0;
    }

    .property-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(min(100%, 290px), 1fr));
      gap: 18px;
      align-items: stretch;
    }

    .result-meta {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 16px;
      color: #b8b8b8;
    }

    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    @media (max-width: 1080px) {
      .layout {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 560px) {
      main {
        padding-top: 34px;
      }

      .result-meta {
        justify-content: stretch;
      }

      .result-meta span,
      .result-meta button {
        width: 100%;
      }
    }
  `],
})
export class PropertiesComponent implements OnInit {
  private readonly propertyService = inject(PropertyService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  properties: Property[] = [];
  filters: PropertyFilters = {};
  loading = true;
  total = 0;
  page = 1;
  hasNext = false;

  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      this.filters = { ...params };
      this.load();
    });
  }

  applyFilters(filters: PropertyFilters): void {
    this.router.navigate(['/imoveis'], { queryParams: filters });
  }

  loadPage(page: number): void {
    this.router.navigate(['/imoveis'], { queryParams: { ...this.filters, page } });
  }

  private load(): void {
    this.loading = true;
    this.page = Number(this.filters.page || 1);
    const request = this.filters.search
      ? this.propertyService.searchProperties(String(this.filters.search), this.filters)
      : this.propertyService.listPublicProperties(this.filters);

    request.subscribe({
      next: (response) => {
        this.properties = response.results;
        this.total = response.count;
        this.hasNext = Boolean(response.next);
        this.loading = false;
      },
      error: () => {
        this.properties = [];
        this.loading = false;
      },
    });
  }
}
