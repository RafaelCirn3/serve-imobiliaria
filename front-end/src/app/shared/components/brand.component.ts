import { Component } from '@angular/core';

@Component({
  selector: 'app-brand', standalone: true,
  template: `<div class="brand" aria-label="SERVE byJB — Negócios Imobiliários, CRECI RESP 15202">
    <div class="main-word">SERVE<span>byJB</span></div>
    <div class="secondary-word">NEGÓCIOS IMOBILIÁRIOS<span>CRECI RESP 15202</span></div>
  </div>`,
  styles: [`
    .brand { display:flex; align-items:center; gap:clamp(12px,2vw,26px); width:max-content; max-width:100%; color:#fff; white-space:nowrap; }
    .main-word { font-family:Arial,sans-serif; font-size:clamp(23px,3.2vw,42px); letter-spacing:.035em; font-weight:400; line-height:1; }
    .main-word span {display:block; font-size:.29em; text-align:right; letter-spacing:0; padding-top:4px; }
    .secondary-word {font-family:Arial,sans-serif; font-size:clamp(9px,1.05vw,14px); font-weight:700; letter-spacing:.035em; line-height:1.15; }
    .secondary-word span {display:block; font-size:.62em; letter-spacing:.06em; margin-top:6px; }
    @media(max-width:560px) { .brand{gap:9px;} .main-word{font-size:clamp(22px,5vw,30px)} .secondary-word{font-size:clamp(8px,2vw,10px)} }
  `]
})
export class BrandComponent {}
