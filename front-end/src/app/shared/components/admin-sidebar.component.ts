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
      <app-brand /><p class="sidebar-caption">ÁREA DE GESTÃO</p>
      <button class="mobile-toggle" type="button" [attr.aria-expanded]="menuOpen" aria-controls="admin-navigation" (click)="menuOpen = !menuOpen">{{ menuOpen ? 'Fechar menu' : 'Menu administrativo' }}</button>
      <nav id="admin-navigation" [class.mobile-open]="menuOpen" (click)="menuOpen = false">
        <a routerLink="/admin/dashboard" routerLinkActive="active">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M4 13h6V4H4v9Zm10 7h6V4h-6v16ZM4 20h6v-4H4v4Z" /></svg>
          </span>
          Visão geral
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
          Contatos recebidos
        </a>
        <a routerLink="/admin/carrosseis" routerLinkActive="active">Vitrines de imóveis</a>
        <a routerLink="/admin/section-images" routerLinkActive="active">Fotos da página inicial</a>
        <a routerLink="/admin/home-content" routerLinkActive="active">Textos da página inicial</a>
        <a routerLink="/admin/banners" routerLinkActive="active">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm2 11h12l-3.6-4.5-2.8 3.4-2-2.4L6 16Zm3-6.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z" /></svg>
          </span>
          Carrossel principal
        </a>
        <a routerLink="/admin/regioes" routerLinkActive="active">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 0-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 0 0-7-7Zm0 9.5A2.5 2.5 0 1 1 12 6a2.5 2.5 0 0 1 0 5.5Z" /></svg>
          </span>
          Regiões
        </a>
      </nav>
      <button type="button" class="logout-button" [class.mobile-visible]="menuOpen" (click)="logout()">Sair</button>
    </aside>
  `,
  styles: [`
    .mobile-toggle { display: none; }
    aside {
      min-height: 100vh;
      padding: 24px;
      border-right: 1px solid #26343b;
      background: #172127;
      position: sticky;
      top: 0;
    }

    .sidebar-caption { color: #657680; font-size: 9px; letter-spacing: .18em; margin: 30px 12px 0; }
    nav {
      display: grid;
      gap: 8px;
      margin: 18px 0 30px;
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
      border-color: #ffffff10;
      background: #ffffff10;
      color: #ffffff;
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
    @media (max-width: 820px) {
      aside { min-height: auto; position: static; padding: 16px; border-right: 0; border-bottom: 1px solid #30363d; }
      aside { display:grid; grid-template-columns:1fr auto; align-items:center; gap:10px; }
      .sidebar-caption { display:none; }
      .mobile-toggle { display:flex; margin:0; width:auto; border-color:#42535c; font-size:12px; min-height:44px; }
      nav { grid-column:1/-1; }
      .logout-button { display:none; grid-column:1/-1; }
      .logout-button.mobile-visible { display:flex; }
      .sidebar-caption { color: #657680; font-size: 9px; letter-spacing: .18em; margin: 30px 12px 0; }
    nav { display: none; margin: 12px 0; }
      nav.mobile-open { display: grid; }
    }
  `],
})
export class AdminSidebarComponent {
  menuOpen = false;
  private readonly auth = inject(AuthService);

  logout(): void {
    this.auth.logout();
  }
}


