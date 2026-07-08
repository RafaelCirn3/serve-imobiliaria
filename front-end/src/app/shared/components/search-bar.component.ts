import { Component, EventEmitter, Output } from '@angular/core';
import { inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';

@Component({
  selector: 'app-search-bar',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="submit()" class="search card">
      <input formControlName="search" placeholder="Busque por bairro, cidade ou descrição">
      <select formControlName="tipo">
        <option value="">Tipo</option>
        <option value="apartamento">Apartamento</option>
        <option value="casa">Casa</option>
        <option value="cobertura">Cobertura</option>
        <option value="terreno">Terreno</option>
        <option value="comercial">Comercial</option>
        <option value="condominio">Condomínio</option>
      </select>
      <input formControlName="bairro" placeholder="Localização">
      <select formControlName="valor_max">
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
      grid-template-columns: 1.5fr 1fr 1fr 1fr auto;
      gap: 10px;
      padding: 12px;
      background: rgba(31, 36, 41, 0.9);
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.28);
    }

    input,
    select {
      min-height: 46px;
      border: 1px solid #30363d;
      border-radius: 8px;
      background: #12161a;
      color: #f5f5f5;
      padding: 0 12px;
      outline: none;
    }

    @media (max-width: 900px) {
      .search {
        grid-template-columns: 1fr 1fr;
      }
    }

    @media (max-width: 560px) {
      .search {
        grid-template-columns: 1fr;
      }
    }
  `],
})
export class SearchBarComponent {
  @Output() filtersChanged = new EventEmitter<Record<string, string>>();
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);

  readonly form = this.fb.nonNullable.group({
    search: [''],
    tipo: [''],
    bairro: [''],
    valor_max: [''],
  });

  submit(): void {
    const filters = this.form.getRawValue();
    this.filtersChanged.emit(filters);
    this.router.navigate(['/imoveis'], { queryParams: filters });
  }
}
