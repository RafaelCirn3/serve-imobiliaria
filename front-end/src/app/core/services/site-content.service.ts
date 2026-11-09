import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '@env/environment';
import { SiteDocument, SitePage } from '@core/models/site-content';
import { SITE_DEFAULTS } from '@core/models/site-defaults';
@Injectable({providedIn:'root'})
export class SiteContentService {
 private readonly http=inject(HttpClient);
 readonly document=signal<SiteDocument>(structuredClone(SITE_DEFAULTS));
 readonly ready=signal(false);
 readonly preview=new URLSearchParams(location.search).get('servePreview')==='1' && window.parent!==window;
 readonly whatsapp=computed(()=>`https://wa.me/${this.text('general','phone')}`);
 private previewReceived=false;
 constructor(){
  this.http.get<SiteDocument>(`${environment.apiUrl}/site-content/`).subscribe({next:value=>{if(!this.previewReceived){this.document.set(value);this.ready.set(true);}},error:()=>this.ready.set(true)});
  if(this.preview){
   window.addEventListener('message',event=>{
    if(event.origin!==location.origin || event.source!==window.parent || event.data?.type!=='serve-customization-preview')return;
    const value=event.data.document as SiteDocument;
    if(!value?.config?.layout || !value.home || !Array.isArray(value.banners))return;
    this.previewReceived=true;this.document.set(value);this.ready.set(true);
    requestAnimationFrame(()=>window.parent.postMessage({type:'serve-preview-applied'},location.origin));
   });
   document.addEventListener('submit',event=>{event.preventDefault();event.stopImmediatePropagation();},true);
   document.addEventListener('click',event=>{const link=(event.target as Element).closest('a');if(!link)return;event.preventDefault();event.stopImmediatePropagation();const url=new URL(link.href,location.origin);if(url.origin===location.origin)window.parent.postMessage({type:'serve-preview-navigate',path:url.pathname},location.origin);},true);
   window.parent.postMessage({type:'serve-preview-ready'},location.origin);
  }
 }
 text(page:SitePage,key:string):string {return this.document().config[page]?.[key] ?? SITE_DEFAULTS.config[page]?.[key] ?? '';}
 section(page:SitePage,id:string){return this.document().config.layout[page]?.find(row=>row.id===id);}
}
