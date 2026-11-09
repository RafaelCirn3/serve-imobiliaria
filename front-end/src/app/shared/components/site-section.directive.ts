import { Directive, ElementRef, effect, inject, input } from '@angular/core';
import { SiteContentService } from '@core/services/site-content.service';
import { SitePage } from '@core/models/site-content';
@Directive({selector:'[appSiteSection]',standalone:true})
export class SiteSectionDirective {
 readonly appSiteSection=input.required<string>();private readonly element=inject(ElementRef<HTMLElement>);private readonly site=inject(SiteContentService);
 constructor(){effect(()=>{
  const [page,id]=this.appSiteSection().split('.') as [SitePage,string];const rows=this.site.document().config.layout[page] || [];const row=rows.find(item=>item.id===id);if(!row)return;
  const host=this.element.nativeElement;host.dataset['siteSection']=this.appSiteSection();host.hidden=!row.visible;
  host.style.setProperty('order',String(page==='general' ? (id==='header' ? -100 : 10000) : rows.findIndex(item=>item.id===id)+1));
  if(row.spacing==='original')host.style.removeProperty('padding-block');else host.style.setProperty('padding-block',({compact:'24px',normal:'48px',wide:'80px'} as Record<string,string>)[row.spacing]);
  if(row.align==='original')host.style.removeProperty('text-align');else host.style.setProperty('text-align',row.align);
  host.dataset['siteTone']=row.tone;host.dataset['siteAlign']=row.align;
 });}
}
