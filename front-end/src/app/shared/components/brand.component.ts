import { Component } from '@angular/core';

@Component({
  selector: 'app-brand',
  standalone: true,
  template: `
    <div class="brand">
      <strong>SERVE</strong>
      <span>negócios imobiliários</span>
    </div>
  `,
  styles: [`
    .brand {
      display: grid;
      gap: 0;
      line-height: 1;
    }

    strong {
      color: #fff;
      font-size: 1.35rem;
      font-weight: 900;
      letter-spacing: 0.08em;
    }

    span {
      color: #c9a24a;
      font-size: 0.64rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }
  `],
})
export class BrandComponent {}
