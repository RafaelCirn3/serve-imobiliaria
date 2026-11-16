import { SiteContentService } from '@core/services/site-content.service';
import { Component, Input, inject } from '@angular/core';

@Component({
  selector: 'app-brand', standalone: true,
  template: `<div class="brand" [attr.aria-label]="site.text('general','brand_name') + ' ' + site.text('general','brand_signature')">
    <img class="brand-logo" [src]="site.text('general','logo') || '/assets/serve-official.svg'" [alt]="site.text('general','brand_name') + ' ' + site.text('general','brand_signature')">
    @if (showSecondary) { <div class="secondary-word">NEGÓCIOS IMOBILIÁRIOS<span>{{site.text('general','creci')}}</span></div> }
  </div>`,
  styles: [`
    .brand { display:flex; align-items:center; gap:clamp(24px,3vw,44px); width:max-content; max-width:100%; color:#fff; white-space:nowrap; }
    .main-word { font-family:Arial,sans-serif; font-size:clamp(23px,3.2vw,42px); letter-spacing:.035em; font-weight:400; line-height:1; }
    .brand-logo { width:clamp(100px,13vw,180px); max-width:100%; height:auto; max-height:68px; object-fit:contain; }
    .main-word span {display:block; font-size:.29em; text-align:right; letter-spacing:0; padding-top:4px; }
    .secondary-word {font-family:Arial,sans-serif; font-size:clamp(10px,.95vw,13px); font-weight:700; letter-spacing:.035em; line-height:1.15; }
    .secondary-word span {display:block; font-size:clamp(8px,.65vw,10px); letter-spacing:.06em; margin-top:6px; }
    @media(max-width:560px) { .brand{gap:14px;} .main-word{font-size:clamp(22px,5vw,30px)} .secondary-word{font-size:clamp(8px,1.8vw,10px)} .secondary-word span{font-size:9px} }
  `]
})
export class BrandComponent { readonly site=inject(SiteContentService); @Input() showSecondary = false; }
