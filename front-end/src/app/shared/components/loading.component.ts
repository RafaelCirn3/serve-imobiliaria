import { Component } from '@angular/core';

@Component({
  selector: 'app-loading',
  standalone: true,
  template: `<div class="loading"><span></span><p>Carregando...</p></div>`,
  styles: [`
    .loading {
      display: grid;
      place-items: center;
      gap: 12px;
      min-height: 180px;
      color: #b8b8b8;
    }

    span {
      width: 38px;
      height: 38px;
      border: 3px solid rgba(255, 255, 255, 0.12);
      border-top-color: #ffffff;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `],
})
export class LoadingComponent {}


