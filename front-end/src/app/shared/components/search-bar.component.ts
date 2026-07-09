import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';

@Component({
  selector: 'app-search-bar',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="submit()" class="search card" [class.hero-search]="variant === 'hero'">
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

    .hero-search {
      max-width: 860px;
      margin-top: 6px;
      border-color: rgba(255, 255, 255, 0.14);
      background: rgba(17, 20, 23, 0.34);
      box-shadow: none;
      backdrop-filter: blur(8px);
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

    .hero-search input,
    .hero-search select {
      min-height: 42px;
      border-color: rgba(255, 255, 255, 0.16);
      background: rgba(17, 20, 23, 0.5);
    }

    .hero-search .btn-primary {
      min-height: 42px;
      background: rgba(255, 255, 255, 0.9);
      color: #111417;
    }

    .hero-search .btn-primary:hover {
      background: #ffffff;
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
  @Input() variant: 'default' | 'hero' = 'default';
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
