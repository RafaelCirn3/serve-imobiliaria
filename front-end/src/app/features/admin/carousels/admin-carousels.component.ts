import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { PropertyCarousel, Property } from '@core/models/api.models';
import { PropertyCarouselService } from '@core/services/property-carousel.service';
import { PropertyService } from '@core/services/property.service';
import { NotificationService } from '@core/services/notification.service';

@Component({
 selector:'app-admin-carousels', standalone:true, imports:[FormsModule],
 template:`
 <div class="admin-page">
   <div class="admin-header"><h1>Carrosséis adicionais</h1></div>
   <p class="muted">Crie seções adicionais com imóveis do catálogo. Apenas imóveis publicados aparecem para visitantes.</p>
   <form class="card editor" (ngSubmit)="save()">
     <label class="field">Título<input name="titulo" [(ngModel)]="titulo" required></label>
     <label class="field">Subtítulo<input name="subtitulo" [(ngModel)]="subtitulo"></label>
     <label class="field">Ordem<input type="number" name="ordem" [(ngModel)]="ordem" min="0"></label>
     <label class="check"><input type="checkbox" name="ativo" [(ngModel)]="ativo"> Ativo</label>
     <fieldset>
       <legend>Imóveis deste carrossel</legend>
       @for (property of properties; track property.id) {
         <label class="choice"><input type="checkbox" [checked]="selected.includes(property.id)" (change)="toggle(property.id,$event)"> {{property.titulo}} — {{property.cidade}}</label>
       }
     </fieldset>
     <div class="actions">
       <button class="btn btn-primary" type="submit" [disabled]="saving || !titulo.trim()"> {{saving ? 'Salvando…' : (editingId ? 'Atualizar' : 'Criar carrossel')}}</button>
       <button class="btn btn-secondary" type="button" (click)="reset()">Limpar</button>
     </div>
   </form>
   <div class="table-wrap"><table><thead><tr><th>Título</th><th>Imóveis</th><th>Ordem</th><th>Ativo</th><th>Ações</th></tr></thead>
   <tbody>@for (carousel of carousels; track carousel.id) {
     <tr><td>{{carousel.titulo}}</td><td>{{carousel.imoveis.length}}</td><td>{{carousel.ordem}}</td><td>{{carousel.ativo ? 'Sim' : 'Não'}}</td>
     <td><button class="btn btn-secondary" type="button" (click)="edit(carousel)">Editar</button>
     <button class="btn btn-danger" type="button" (click)="remove(carousel)">Excluir</button></td></tr>
   }</tbody></table></div>
 </div>
 `,
 styles:[`.editor{display:grid;gap:12px;padding:20px;margin-bottom:24px}.choice{display:block;padding:6px}fieldset{max-height:290px;overflow:auto;border:1px solid #444}.actions{display:flex;gap:12px}.check{display:flex;gap:8px}`]
})
export class AdminCarouselsComponent implements OnInit {
 private readonly service=inject(PropertyCarouselService);
 private readonly propertiesService=inject(PropertyService);
 private readonly notification=inject(NotificationService);
 carousels: PropertyCarousel[]=[];
 properties: Property[]=[];
 titulo=''; subtitulo=''; ordem=0; ativo=true; selected:number[]=[]; editingId:number|null=null; saving=false;
 ngOnInit(){this.load();this.loadProperties(1);}
 loadProperties(page:number) {
   this.propertiesService.listAdminProperties({page}).subscribe({next:r=>{
      this.properties=[...this.properties,...r.results];
      if(r.next) this.loadProperties(page+1);
   }});
 }
 load(){this.service.list(true).subscribe({next:r=>this.carousels=r.results});}
 toggle(id:number,event:Event){const checked=(event.target as HTMLInputElement).checked;
   this.selected=checked ? [...this.selected,id] : this.selected.filter(v=>v!==id);}
 edit(c:PropertyCarousel){this.editingId=c.id;this.titulo=c.titulo;this.subtitulo=c.subtitulo;this.ordem=c.ordem;this.ativo=c.ativo;this.selected=[...c.imoveis];}
 reset(){this.editingId=null;this.titulo='';this.subtitulo='';this.ordem=0;this.ativo=true;this.selected=[];}
 save(){if(this.saving || !this.titulo.trim())return;this.saving=true;
   const payload={titulo:this.titulo,subtitulo:this.subtitulo,ordem:this.ordem,ativo:this.ativo,imoveis:this.selected};
   const req=this.editingId?this.service.update(this.editingId,payload):this.service.create(payload);
   req.subscribe({next:()=>{this.saving=false;this.reset();this.load();this.notification.show({type:'success',text:'Carrossel salvo.'});},
   error:()=>{this.saving=false;this.notification.show({type:'error',text:'Falha ao salvar carrossel.'});}});
 }
 remove(c:PropertyCarousel){if(!confirm('Excluir este carrossel?'))return;this.service.remove(c.id).subscribe({next:()=>this.load()});}
}
