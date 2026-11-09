import { Component } from '@angular/core';

@Component({
  selector: 'app-admin-topbar',
  standalone: true,
  template: `
    <header>
      <div>
        <strong>Painel SERVE</strong>
        <span>Seu portfólio, organizado.</span>
      </div>
      <a class="view-site" href="/" target="_blank">Ver site ↗</a>
    </header>
  `,
  styles: [`
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      border-bottom: 1px solid #e2e7eb;
      padding: 18px 24px;
      background: rgba(255, 255, 255, 0.96);
      backdrop-filter: blur(14px);
      position: sticky;
      top: 0;
      z-index: 10;
    }

    .view-site { color: #4b5f6c; background: #fff; border: 1px solid #d9e1e7; border-radius: 7px; padding: 10px 14px; font-size: 12px; white-space: nowrap; }
    div {
      display: grid;
      gap: 2px;
    }

    span {
      color: #7c8890;
      font-size: 0.86rem;
    }
    @media(max-width:820px) { header {padding:12px 16px;} span {display:none;} strong {font-size:12px;} }
  `],
})
export class AdminTopbarComponent {}


