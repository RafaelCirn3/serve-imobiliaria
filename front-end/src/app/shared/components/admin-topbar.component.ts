import { Component } from '@angular/core';

@Component({
  selector: 'app-admin-topbar',
  standalone: true,
  template: `
    <header>
      <div>
        <strong>Painel SERVE</strong>
        <span>Gestão exclusiva do administrador</span>
      </div>
      <a class="btn btn-secondary" href="/" target="_blank">Ver site</a>
    </header>
  `,
  styles: [`
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      border-bottom: 1px solid #30363d;
      padding: 18px 24px;
      background: rgba(24, 28, 32, 0.76);
      backdrop-filter: blur(14px);
      position: sticky;
      top: 0;
      z-index: 10;
    }

    div {
      display: grid;
      gap: 2px;
    }

    span {
      color: #b8b8b8;
      font-size: 0.86rem;
    }
  `],
})
export class AdminTopbarComponent {}


