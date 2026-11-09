import { SiteContentService } from '@core/services/site-content.service';
import { SiteSectionDirective } from '@shared/components/site-section.directive';
import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { BrandComponent } from './brand.component';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [SiteSectionDirective, RouterLink, RouterLinkActive, BrandComponent],
  template: `
    <header class="site-header" appSiteSection="general.header">
      <div class="container nav">
        <a routerLink="/" aria-label="Início SERVE"><app-brand [showSecondary]="router.url.split('?')[0] === '/'" /></a>
        <nav>
          <a routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: true }">{{site.text('general','nav_home')}}</a>
          <a routerLink="/imoveis" routerLinkActive="active">{{site.text('general','nav_properties')}}</a>
          <a routerLink="/sobre" routerLinkActive="active">{{site.text('general','nav_about')}}</a>
          <a routerLink="/contato" routerLinkActive="active">{{site.text('general','nav_contact')}}</a>
        </nav>
      </div>
    </header>
  `,
  styles: [`
    .site-header {
      position: sticky;
      top: 0;
      z-index: 20;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(17, 20, 23, 0.78);
      backdrop-filter: blur(18px);
    }

    .nav {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      min-height: 74px;
    }

    nav {
      display: flex;
      align-items: center;
      gap: 22px;
      color: #d8d8d8;
      font-size: 0.92rem;
      font-weight: 700;
    }

    nav a {
      position: relative;
      padding: 8px 0;
      transition: color 0.18s ease;
      white-space: nowrap;
    }

    nav a::after {
      content: '';
      position: absolute;
      left: 0;
      right: 0;
      bottom: 1px;
      height: 2px;
      border-radius: 999px;
      background: linear-gradient(90deg, transparent, #ffffff, transparent);
      transform: scaleX(0);
      transform-origin: center;
      transition: transform 0.24s ease;
    }

    nav a:hover,
    nav a.active {
      color: #ffffff;
    }

    nav a:hover::after,
    nav a.active::after {
      transform: scaleX(1);
    }

    @media (max-width: 860px) {
      .nav {
        flex-wrap: wrap;
        padding: 14px 0;
      }

      nav {
        order: 3;
        width: 100%;
        overflow-x: auto;
        padding-bottom: 4px;
        scrollbar-width: none;
        scroll-snap-type: x proximity;
      }

      nav::-webkit-scrollbar {
        display: none;
      }

      nav a {
        scroll-snap-align: start;
      }
    }
  `],
})
export class HeaderComponent { readonly site=inject(SiteContentService); readonly router = inject(Router); }


