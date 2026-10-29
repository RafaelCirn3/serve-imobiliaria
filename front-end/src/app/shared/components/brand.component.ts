import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-brand', standalone: true,
  template: `<div class="brand" [attr.aria-label]="showSecondary ? 'SERVE byJB — Negócios Imobiliários, CRECI RESP 15202' : 'SERVE byJB'">
    <div class="main-word">SERVE<span>byJB</span></div>
    @if (showSecondary) { <div class="secondary-word">NEGÓCIOS IMOBILIÁRIOS<span>CRECI RESP 15202</span></div> }
  </div>`,
  styles: [`
    .brand { display:flex; align-items:center; gap:clamp(24px,3vw,44px); width:max-content; max-width:100%; color:#fff; white-space:nowrap; }
    .main-word { font-family:Arial,sans-serif; font-size:clamp(23px,3.2vw,42px); letter-spacing:.035em; font-weight:400; line-height:1; }
    .main-word span {display:block; font-size:.29em; text-align:right; letter-spacing:0; padding-top:4px; }
    .secondary-word {font-family:Arial,sans-serif; font-size:clamp(10px,.95vw,13px); font-weight:700; letter-spacing:.035em; line-height:1.15; }
    .secondary-word span {display:block; font-size:clamp(8px,.65vw,10px); letter-spacing:.06em; margin-top:6px; }
    @media(max-width:560px) { .brand{gap:14px;} .main-word{font-size:clamp(22px,5vw,30px)} .secondary-word{font-size:clamp(8px,1.8vw,10px)} .secondary-word span{font-size:9px} }
  `]
})
export class BrandComponent { @Input() showSecondary = false; }
