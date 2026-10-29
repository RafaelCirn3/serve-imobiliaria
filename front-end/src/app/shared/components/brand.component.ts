import { Component } from '@angular/core';

@Component({
  selector: 'app-brand',
  standalone: true,
  template: `
    <div class="brand">
      <img src="assets/serve-primary.svg" alt="Serve Negócios Imobiliários">
    </div>
  `,
  styles: [`
    .brand {
      width: clamp(185px, 18vw, 245px);
      height: 62px;
    }

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      object-position: left center;
    }

  `],
})
export class BrandComponent {}


