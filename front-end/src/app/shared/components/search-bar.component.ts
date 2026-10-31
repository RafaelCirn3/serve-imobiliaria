import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { PROPERTY_TYPES, SERVICE_CITIES } from '@core/models/property-options';
import { LocationFiltersComponent } from './location-filters.component';

@Component({
  selector: 'app-search-bar',
  standalone: true,
  imports: [ReactiveFormsModule, LocationFiltersComponent],
  template: `
    <form [formGroup]="form" (ngSubmit)="submit()" class="search" [class.hero-search]="variant === 'hero'">
      <input formControlName="search" aria-label="Busca" placeholder="Busque por bairro, cidade ou descrição">
      @if (variant === 'hero') {
        <select formControlName="finalidade" aria-label="Finalidade">
          <option value="">Comprar ou alugar</option>
          <option value="venda">Comprar</option>
          <option value="aluguel">Alugar</option>
        </select>
      }
      <select formControlName="tipo" aria-label="Tipo de imóvel">
        <option value="">Todos os tipos</option>
        @for (type of propertyTypes; track type.value) {
          <option [value]="type.value">{{ type.label }}</option>
        }
      </select>
      <app-location-filters [form]="form" [compact]="true" />
      <select formControlName="valor_max" aria-label="Valor máximo">
        <option value="">Faixa de preço</option>
        <option value="500000">Até R$ 500 mil</option>
        <option value="900000">Até R$ 900 mil</option>
        <option value="1500000">Até R$ 1,5 mi</option>
      </select>
      <button class="btn btn-primary" type="submit">Buscar</button>
    </form>
  `,
  styles: [`
    .search {
      display: grid;
      grid-template-columns: 1.3fr 1fr 3fr 1fr auto;
      align-items: end;
      gap: 10px;
      padding: 12px;
      background: transparent;
      border: 0;
      box-shadow: none;
    }

    .hero-search {
      width: 100%;
      margin: 0;
      padding: 0;
      grid-template-columns: minmax(180px,1.5fr) minmax(115px,.8fr) minmax(140px,1fr) minmax(225px,1.6fr) minmax(140px,1fr) auto;
      background: transparent;
      border: 0;
      box-shadow: none;
      backdrop-filter: none;
    }

    input,
    select {
      width: 100%;
      min-width: 0;
      min-height: 46px;
      border: 1px solid #30363d;
      border-radius: 8px;
      background: #12161a;
      color: #f5f5f5;
      padding: 0 12px;
      outline: none;
    }

    .hero-search input,
    .hero-search select {
      min-height: 42px;
      border-color: rgba(255, 255, 255, 0.16);
      background: #111417;
    }

    .hero-search .btn-primary {
      min-height: 46px;
      background: #f5f5f5;
      color: #111417;
    }

    .hero-search .btn-primary:hover {
      background: #ffffff;
    }

    @media (max-width: 1120px) {
      .hero-search { grid-template-columns: repeat(3,minmax(0,1fr)); }
      .hero-search app-location-filters { grid-column: span 2; }
    }
    @media (max-width: 900px) {
      .search {
        grid-template-columns: 1fr 1fr;
      }
      .search app-location-filters { grid-column: 1 / -1; }
      .hero-search { grid-template-columns: 1fr 1fr; }
    }

    @media (max-width: 560px) {
      .search {
        grid-template-columns: 1fr;
      }
      .hero-search { grid-template-columns: 1fr; }
    }
  `],
})
export class SearchBarComponent {
  readonly propertyTypes = PROPERTY_TYPES;
  readonly cities = SERVICE_CITIES;
  @Input() variant: 'default' | 'hero' = 'default';
  @Output() filtersChanged = new EventEmitter<Record<string, string>>();
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);

  readonly form = this.fb.nonNullable.group({
    search: [''],
    tipo: [''],
    finalidade: [''],
    cidade: [''],
    bairro: [''],
    logradouro: [''],
    valor_max: [''],
  });

  submit(): void {
    const filters = this.form.getRawValue();
    this.filtersChanged.emit(filters);
    this.router.navigate(['/imoveis'], { queryParams: filters });
  }
}
