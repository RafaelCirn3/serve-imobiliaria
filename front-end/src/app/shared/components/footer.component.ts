import { SiteContentService } from '@core/services/site-content.service';
import { SiteSectionDirective } from '@shared/components/site-section.directive';
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { BrandComponent } from './brand.component';

@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [SiteSectionDirective, RouterLink, BrandComponent],
  template: `
    <footer appSiteSection="general.footer">
      <div class="container footer-grid">
        <div>
          <app-brand />
          <small class="footer-creci">{{site.text('general','creci')}}</small>
          <p>{{site.text('general','footer_description')}}</p>
        </div>
        <div>
          <strong>{{site.text('general','footer_nav')}}</strong>
          <a routerLink="/imoveis">{{site.text('general','nav_properties')}}</a>
          <a routerLink="/sobre">{{site.text('general','nav_about')}}</a>
          <a routerLink="/contato">{{site.text('general','nav_contact')}}</a>
          <a routerLink="/admin">{{site.text('general','nav_login')}}</a>
        </div>
        <div>
          <strong>{{site.text('general','footer_contact')}}</strong>
          <a [href]="site.whatsapp()" target="_blank" rel="noopener noreferrer">WhatsApp: {{site.text('general','phone_label')}}</a>
          <a [href]="'mailto:' + site.text('general','email')">{{site.text('general','email')}}</a>
          <span>{{site.text('general','service_area')}}</span>
        </div>
      </div>
    </footer>
  `,
  styles: [`
    footer {
      border-top: 1px solid #30363d;
      background: #0d1013;
      padding: 44px 0;
    }

    .footer-grid {
      display: grid;
      grid-template-columns: 1.5fr 1fr 1fr;
      gap: 28px;
    }

    p,
    span,
    a {
      color: #b8b8b8;
      line-height: 1.7;
      overflow-wrap: anywhere;
    }

    .footer-creci {
      display: block;
      margin: 8px 0 14px;
      color: #ffffff;
      font-size: 0.72rem;
      font-weight: 800;
      letter-spacing: 0.08em;
    }

    strong {
      display: block;
      margin-bottom: 12px;
      color: #fff;
    }

    a,
    span {
      display: block;
      margin: 6px 0;
    }

    @media (max-width: 760px) {
      .footer-grid {
        grid-template-columns: 1fr;
      }
    }
  `],
})
export class FooterComponent { readonly site=inject(SiteContentService);}


