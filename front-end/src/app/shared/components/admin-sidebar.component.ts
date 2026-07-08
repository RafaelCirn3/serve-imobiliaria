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
        <a routerLink="/admin/dashboard" routerLinkActive="active">Dashboard</a>
        <a routerLink="/admin/imoveis" routerLinkActive="active">Imóveis</a>
        <a routerLink="/admin/leads" routerLinkActive="active">Leads</a>
        <a routerLink="/admin/banners" routerLinkActive="active">Banners</a>
        <a routerLink="/admin/regioes" routerLinkActive="active">Regiões</a>
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
