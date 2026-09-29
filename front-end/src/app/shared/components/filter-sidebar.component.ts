import { Component, EventEmitter, Input, OnChanges, Output, inject } from '@angular/core';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { PropertyFilters } from '@core/models/api.models';
import { PROPERTY_TYPES, SERVICE_CITIES } from '@core/models/property-options';

function validRanges(control: AbstractControl): ValidationErrors | null {
  const values = control.value as Record<string, string>;
  for (const [minimum, maximum] of [
    ['valor_min', 'valor_max'], ['area_min', 'area_max'], ['area_total_min', 'area_total_max'],
  ]) {
    if (values[minimum] !== '' && values[maximum] !== '' && Number(values[minimum]) > Number(values[maximum])) {
      return { invalidRange: true };
    }
  }
  return null;
}

@Component({
  selector: 'app-filter-sidebar',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form class="filters card" [formGroup]="form" (ngSubmit)="apply()">
      <h2>Filtros</h2>
      <label>Busca<input formControlName="search" placeholder="Título, bairro ou cidade"></label>
      <label>Cidade
        <select formControlName="cidade" (change)="form.controls.bairro.setValue('')">
          <option value="">Todas as cidades</option>
          @for (city of cities; track city) { <option [value]="city">{{ city }}</option> }
        </select>
      </label>
      <label>Bairro<input formControlName="bairro" placeholder="Bessa, Manaira..."></label>
      <label>Tipo
        <select formControlName="tipo">
          <option value="">Todos</option>
          @for (type of propertyTypes; track type.value) {
            <option [value]="type.value">{{ type.label }}</option>
          }
        </select>
      </label>
      <label>Finalidade
        <select formControlName="finalidade">
          <option value="">Todas</option>
          <option value="venda">Venda</option>
          <option value="aluguel">Aluguel</option>
        </select>
      </label>
      <div class="pair">
        <label>Valor mínimo (R$)<input type="number" min="0" step="0.01" formControlName="valor_min"></label>
        <label>Valor máximo (R$)<input type="number" min="0" step="0.01" formControlName="valor_max"></label>
      </div>
      <div class="pair">
        <label>Quartos (mín.)<input type="number" min="0" step="1" formControlName="quartos"></label>
        <label>Vagas (mín.)<input type="number" min="0" step="1" formControlName="vagas"></label>
      </div>
      <div class="pair">
        <label>Área privativa mín. (m²)<input type="number" min="0" step="0.01" formControlName="area_min"></label>
        <label>Área privativa máx. (m²)<input type="number" min="0" step="0.01" formControlName="area_max"></label>
      </div>
      <div class="pair">
        <label>Área total mín. (m²)<input type="number" min="0" step="0.01" formControlName="area_total_min"></label>
        <label>Área total máx. (m²)<input type="number" min="0" step="0.01" formControlName="area_total_max"></label>
      </div>
      <p class="hint">Para áreas e terrenos, use a área total. As faixas preenchidas são combinadas.</p>
      @if (form.invalid) {
        <p class="validation-error" role="alert">Use valores não negativos e máximos maiores ou iguais aos mínimos.</p>
      }
      <label>Ordenar
        <select formControlName="ordering">
          <option value="">Relevancia</option>
          <option value="valor">Menor preço</option>
          <option value="-valor">Maior preço</option>
          <option value="-publicado_em">Mais recentes</option>
          <option value="-destaque">Destaques</option>
        </select>
      </label>
      <div class="actions">
        <button class="btn btn-primary" type="submit" [disabled]="form.invalid">Aplicar</button>
        <button class="btn btn-secondary" type="button" (click)="clear()">Limpar</button>
      </div>
    </form>
  `,
  styles: [`
    .filters {
      display: grid;
      gap: 14px;
      min-width: 0;
      padding: 18px;
      position: sticky;
      top: 96px;
    }

    h2 {
      margin: 0;
    }

    .hint, .validation-error {
      margin: 0;
      font-size: 0.8rem;
      line-height: 1.5;
      color: #b8b8b8;
    }

    .validation-error { color: #ffb4b4; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }

    label {
      display: grid;
      gap: 7px;
      min-width: 0;
      color: #b8b8b8;
      font-size: 0.86rem;
      font-weight: 800;
    }

    input,
    select {
      width: 100%;
      min-width: 0;
      min-height: 42px;
      border: 1px solid #30363d;
      border-radius: 8px;
      background: #12161a;
      color: #f5f5f5;
      padding: 0 10px;
      outline: none;
    }

    .pair {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    .actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    @media (max-width: 1080px) {
      .filters {
        position: static;
      }
    }

    @media (max-width: 560px) {
      .pair,
      .actions {
        grid-template-columns: 1fr;
      }
    }
  `],
})
export class FilterSidebarComponent implements OnChanges {
  readonly propertyTypes = PROPERTY_TYPES;
  readonly cities = SERVICE_CITIES;
  @Input() initialFilters: PropertyFilters = {};
  @Output() filtersChanged = new EventEmitter<PropertyFilters>();
  private readonly fb = inject(FormBuilder);

  readonly form = this.fb.nonNullable.group({
    search: [''],
    cidade: [''],
    bairro: [''],
    tipo: [''],
    finalidade: [''],
    valor_min: ['', Validators.min(0)],
    valor_max: ['', Validators.min(0)],
    quartos: ['', Validators.min(0)],
    vagas: ['', Validators.min(0)],
    area_min: ['', Validators.min(0)],
    area_max: ['', Validators.min(0)],
    area_total_min: ['', Validators.min(0)],
    area_total_max: ['', Validators.min(0)],
    ordering: [''],
  }, { validators: validRanges });

  ngOnChanges(): void {
    this.form.reset(undefined, { emitEvent: false });
    this.form.patchValue(this.initialFilters as Record<string, string>, { emitEvent: false });
  }

  apply(): void {
    if (this.form.invalid) return;
    this.filtersChanged.emit(this.form.getRawValue());
  }

  clear(): void {
    this.form.reset();
    this.filtersChanged.emit({});
  }
}


