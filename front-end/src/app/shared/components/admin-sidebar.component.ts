import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '@core/services/auth.service';
import { BrandComponent } from './brand.component';

@Component({
  selector: 'app-admin-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, BrandComponent],
  template: `
    <aside>
      <app-brand />
      <nav>
        <a routerLink="/admin/dashboard" routerLinkActive="active">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M4 13h6V4H4v9Zm10 7h6V4h-6v16ZM4 20h6v-4H4v4Z" /></svg>
          </span>
          Dashboard
        </a>
        <a routerLink="/admin/imoveis" routerLinkActive="active">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M3 11.5 12 4l9 7.5v8a1 1 0 0 1-1 1h-5.5v-6h-5v6H4a1 1 0 0 1-1-1v-8Z" /></svg>
          </span>
          Imóveis
        </a>
        <a routerLink="/admin/leads" routerLinkActive="active">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-8 8a8 8 0 0 1 16 0v1H4v-1Z" /></svg>
          </span>
          Leads
        </a>
        <a routerLink="/admin/banners" routerLinkActive="active">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm2 11h12l-3.6-4.5-2.8 3.4-2-2.4L6 16Zm3-6.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z" /></svg>
          </span>
          Banners
        </a>
        <a routerLink="/admin/regioes" routerLinkActive="active">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 0-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 0 0-7-7Zm0 9.5A2.5 2.5 0 1 1 12 6a2.5 2.5 0 0 1 0 5.5Z" /></svg>
          </span>
          Regiões
        </a>
      </nav>
      <button type="button" (click)="logout()">Sair</button>
    </aside>
  `,
  styles: [`
    aside {
      min-height: 100vh;
      padding: 24px;
      border-right: 1px solid #30363d;
      background: #0d1013;
      position: sticky;
      top: 0;
    }

    nav {
      display: grid;
      gap: 8px;
      margin: 34px 0;
    }

    a,
    button {
      display: flex;
      align-items: center;
      gap: 10px;
      border: 1px solid transparent;
      border-radius: 8px;
      background: transparent;
      color: #b8b8b8;
      padding: 12px;
      text-align: left;
      font-weight: 800;
    }

    a.active,
    a:hover {
      border-color: rgba(201, 162, 74, 0.35);
      background: rgba(201, 162, 74, 0.1);
      color: #c9a24a;
    }

    .icon {
      display: inline-grid;
      flex: 0 0 20px;
      place-items: center;
      width: 20px;
      height: 20px;
    }

    .icon svg {
      width: 20px;
      height: 20px;
      fill: currentColor;
    }

    button {
      width: 100%;
      border-color: #30363d;
    }
  `],
})
export class AdminSidebarComponent {
  private readonly auth = inject(AuthService);

  logout(): void {
    this.auth.logout();
  }
}
