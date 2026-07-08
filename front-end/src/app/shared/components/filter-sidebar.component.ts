import { Component, EventEmitter, Input, OnChanges, Output, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { PropertyFilters } from '@core/models/api.models';

@Component({
  selector: 'app-filter-sidebar',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form class="filters card" [formGroup]="form" (ngSubmit)="apply()">
      <h2>Filtros</h2>
      <label>Busca<input formControlName="search" placeholder="Título, bairro ou cidade"></label>
      <label>Cidade<input formControlName="cidade" placeholder="João Pessoa"></label>
      <label>Bairro<input formControlName="bairro" placeholder="Bessa, Manaira..."></label>
      <label>Tipo
        <select formControlName="tipo">
          <option value="">Todos</option>
          <option value="apartamento">Apartamento</option>
          <option value="casa">Casa</option>
          <option value="cobertura">Cobertura</option>
          <option value="terreno">Terreno</option>
          <option value="comercial">Comercial</option>
          <option value="condominio">Condomínio</option>
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
        <label>Valor min<input type="number" formControlName="valor_min"></label>
        <label>Valor max<input type="number" formControlName="valor_max"></label>
      </div>
      <div class="pair">
        <label>Quartos<input type="number" formControlName="quartos"></label>
        <label>Vagas<input type="number" formControlName="vagas"></label>
      </div>
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
        <button class="btn btn-primary" type="submit">Aplicar</button>
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
  @Input() initialFilters: PropertyFilters = {};
  @Output() filtersChanged = new EventEmitter<PropertyFilters>();
  private readonly fb = inject(FormBuilder);

  readonly form = this.fb.nonNullable.group({
    search: [''],
    cidade: [''],
    bairro: [''],
    tipo: [''],
    finalidade: [''],
    valor_min: [''],
    valor_max: [''],
    quartos: [''],
    vagas: [''],
    ordering: [''],
  });

  ngOnChanges(): void {
    this.form.patchValue(this.initialFilters as Record<string, string>, { emitEvent: false });
  }

  apply(): void {
    this.filtersChanged.emit(this.form.getRawValue());
  }

  clear(): void {
    this.form.reset();
    this.filtersChanged.emit({});
  }
}
