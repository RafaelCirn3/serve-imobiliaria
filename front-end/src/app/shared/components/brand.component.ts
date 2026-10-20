import { Component } from '@angular/core';

@Component({
  selector: 'app-brand',
  standalone: true,
  template: `
    <div class="brand">
      <img src="assets/serve-logo.png" alt="Serve Negócios Imobiliários">
    </div>
  `,
  styles: [`
    .brand {
      width: clamp(170px, 20vw, 240px);
      height: 68px;
    }

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      object-position: center;
    }

  `],
})
export class BrandComponent {}


