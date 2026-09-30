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
      width: 190px;
      height: 58px;
      overflow: hidden;
    }

    img {
      width: 100%;
      height: 58px;
      object-fit: cover;
      object-position: center;
    }

  `],
})
export class BrandComponent {}


