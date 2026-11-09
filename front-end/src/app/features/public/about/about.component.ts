import { Component, inject } from '@angular/core';
import { SiteContentService } from '@core/services/site-content.service';
import { mediaUrl } from '@core/services/media-url';
import { SiteSectionDirective } from '@shared/components/site-section.directive';
import { HeaderComponent } from '@shared/components/header.component';
import { FooterComponent } from '@shared/components/footer.component';
@Component({selector:'app-about',standalone:true,imports:[SiteSectionDirective,HeaderComponent,FooterComponent],
 template:`<div class="page-shell"><app-header/><main data-site-page="about">
  <section class="hero" appSiteSection="about.hero" [style.background-image]="'linear-gradient(180deg,#11141733,#111417),url(' + mediaUrl(site.text('about','hero_image')) + ')'">
   <div class="container"><span class="eyebrow">{{site.text('about','label')}}</span><h1>{{site.text('about','title')}}</h1></div>
  </section>
  <section class="section" appSiteSection="about.story"><div class="container story"><h2 class="section-title">{{site.text('about','heading')}}</h2><p>{{site.text('about','body')}}</p><p>{{site.text('about','extra')}}</p></div></section>
  <section class="section" appSiteSection="about.values"><div class="container"><h2>{{site.text('about','values_title')}}</h2><div class="values">@for (key of ['value_1','value_2','value_3','value_4'];track key) { <div class="card">{{site.text('about',key)}}</div> }</div></div></section>
 </main><app-footer/></div>`,
 styles:[`.hero{min-height:460px;display:grid;align-items:end;padding:90px 0 64px;background-position:center;background-size:cover}.hero h1{max-width:860px;margin:12px 0 0;font-size:clamp(2.5rem,6vw,5.4rem);line-height:1}.story{max-width:1000px}p{line-height:1.8;color:#b8b8b8;white-space:pre-line}.values{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.values .card{padding:24px;line-height:1.7}@media(max-width:600px){.values{grid-template-columns:1fr}.hero{min-height:360px}}`],})
export class AboutComponent {readonly site=inject(SiteContentService);readonly mediaUrl=mediaUrl;}
