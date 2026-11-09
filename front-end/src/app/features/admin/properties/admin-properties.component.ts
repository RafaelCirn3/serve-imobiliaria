import { CurrencyPipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Property } from '@core/models/api.models';
import { PROPERTY_TYPES, propertyTypeLabel } from '@core/models/property-options';
import { NotificationService } from '@core/services/notification.service';
import { PropertyService } from '@core/services/property.service';
import { ConfirmDialogComponent } from '@shared/components/confirm-dialog.component';
import { PhotoComponent } from '@shared/components/photo.component';

@Component({
 selector: 'app-admin-properties', standalone: true,
 imports: [CurrencyPipe, FormsModule, RouterLink, ConfirmDialogComponent, PhotoComponent],
 template: `
  <div class="admin-page">
    <div class="admin-header"><div><span class="admin-eyebrow">PORTFÓLIO</span><h1>Seus imóveis</h1><p class="muted">Encontre um imóvel pela foto e continue de onde parou.</p></div><a class="btn btn-primary" routerLink="/admin/imoveis/novo">+ Novo imóvel</a></div>
    <form class="card filters" (ngSubmit)="load(1)">
      <label class="field">Buscar imóvel<input name="search" [(ngModel)]="search" placeholder="Título, bairro ou cidade"></label>
      <label class="field">Publicação<select name="status" [(ngModel)]="status"><option value="">Todos os status</option><option value="publicado">Publicado</option><option value="rascunho">Rascunho</option><option value="vendido">Vendido</option><option value="alugado">Alugado</option><option value="inativo">Inativo</option></select></label>
      <label class="field">Tipo<select name="tipo" [(ngModel)]="tipo"> <option value="">Todos os tipos</option>@for (type of propertyTypes; track type.value) { <option [value]="type.value">{{ type.label }}</option> }</select></label>
      <button class="btn btn-secondary" type="submit" [disabled]="loading">Buscar</button>
      <button class="clear" type="button" (click)="clear()">Limpar</button>
    </form>
    @if (error) { <div class="admin-notice error" role="alert">{{ error }} <button class="btn btn-secondary" (click)="load(page)">Tentar novamente</button></div> }
    @if (loading) { <div class="admin-empty" role="status">Carregando seus imóveis…</div> } @else {
      <div class="list-heading"><span>{{ count }} imóvel(is) encontrado(s)</span><span class="muted">Fotos e informações do cadastro</span></div>
      <div class="property-grid">
        @for (property of properties; track property.id) {
          <article class="card property-tile">
            <a class="tile-photo" [routerLink]="['/admin/imoveis',property.id,'editar']" [attr.aria-label]="'Editar ' + property.titulo"><app-photo [src]="cover(property)" [alt]="property.titulo" [eager]="true" /><span class="photo-count">{{ property.imagens.length }} foto(s)</span></a>
            <div class="tile-body"><div class="tile-meta"><span class="admin-badge" [attr.data-status]="property.status">{{ statusLabel(property.status) }}</span><span class="muted">#{{ property.id }}</span></div>
              <h2><a [routerLink]="['/admin/imoveis',property.id,'editar']">{{ property.titulo }}</a></h2>
              <p class="muted">{{ property.bairro }} · {{ property.cidade }}</p><strong class="tile-price">{{ numberValue(property.valor) | currency:'BRL':'symbol':'1.0-0':'pt-BR' }}</strong>
              <p class="tile-details">{{ typeLabel(property.tipo) }} · {{ property.finalidade === 'venda' ? 'Venda' : 'Aluguel' }}</p>
              @if (!property.imagens.length) { <p class="photo-warning">! Adicione fotos para apresentar este imóvel.</p> }
              <div class="tile-actions"><a class="btn btn-primary" [routerLink]="['/admin/imoveis',property.id,'editar']">Editar imóvel</a>@if (property.status === 'publicado') { <a class="btn btn-secondary" [routerLink]="['/imoveis',property.slug]" target="_blank" rel="noopener">Ver no site ↗</a> }<button class="clear" type="button" [disabled]="property.status === 'inativo'" (click)="selected = property">Inativar</button></div>
            </div>
          </article>
        } @empty { <div class="admin-empty card"><h2>Nenhum imóvel encontrado</h2><p>Altere os filtros ou cadastre seu primeiro imóvel.</p><a routerLink="/admin/imoveis/novo" class="btn btn-primary">Cadastrar imóvel</a></div> }
      </div>
      @if (count > 12) { <nav class="pagination" aria-label="Páginas de imóveis"><button class="btn btn-secondary" [disabled]="!previous" (click)="load(page - 1)">← Anterior</button><span>Página {{ page }} de {{ pages }}</span><button class="btn btn-secondary" [disabled]="!next" (click)="load(page + 1)">Próxima →</button></nav> }
    }
  </div>
  <app-confirm-dialog [open]="!!selected" title="Inativar imóvel" message="O imóvel será mantido no painel e deixará de aparecer no site." (cancel)="selected = null" (confirm)="deleteSelected()" />
 `,
 styles: [`
  .filters { display: grid; grid-template-columns: minmax(180px,2fr) 1fr 1fr auto auto; align-items: end; gap: 14px; padding: 20px; }
  .clear { border: 0; background: transparent; color: #53616d; min-height: 44px; text-decoration: underline; }
  .list-heading,.tile-meta,.pagination { display:flex; align-items:center; justify-content:space-between; gap:12px; font-size:13px; }
  .property-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:20px; }
  .property-tile { overflow:hidden; display:flex; flex-direction:column; }
  .tile-photo { position:relative; display:block; aspect-ratio:16/10; }
  .photo-count { position:absolute; bottom:12px; right:12px; background:#111a; color:white; border-radius:6px; padding:5px 8px; font-size:12px; }
  .tile-body { display:flex; flex-direction:column; gap:12px; padding:20px; flex:1; }
  h2 { font-size:17px; line-height:1.4; margin:0; } p { margin:0; font-size:13px; line-height:1.6; } .tile-price { font-size:21px; font-weight:750; }
  .tile-details { color:#56626d; } .tile-actions { display:flex; gap:8px; flex-wrap:wrap; margin-top:auto; padding-top:12px; border-top:1px solid #edf0f2; }
  .tile-actions .btn { font-size:12px; padding:0 12px; } .photo-warning { color:#8c5d13; background:#fff8e8; padding:8px; border-radius:6px; }
  .pagination { justify-content:center; padding:12px; }
  @media(max-width:1200px) { .property-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .filters { grid-template-columns:1fr 1fr; } }
  @media(max-width:560px) { .property-grid,.filters { grid-template-columns:1fr; } .list-heading { flex-wrap:wrap; } }
 `],
})
export class AdminPropertiesComponent implements OnInit {
 readonly propertyTypes = PROPERTY_TYPES; readonly typeLabel = propertyTypeLabel;
 private readonly service = inject(PropertyService); private readonly notification = inject(NotificationService);
 properties: Property[] = []; selected: Property | null = null;
 search = ''; status = ''; tipo = ''; page = 1; count = 0; next = false; previous = false; loading = false; error = '';
 get pages(): number { return Math.ceil(this.count / 12); }
 ngOnInit(): void { this.load(); }
 cover(property: Property): string { return property.imagens.find(image => image.imagem_capa)?.imagem || property.imagens[0]?.imagem || ''; }
 statusLabel(status?: string): string { return ({publicado:'Publicado',rascunho:'Rascunho',vendido:'Vendido',alugado:'Alugado',inativo:'Inativo'} as Record<string,string>)[status || ''] || 'Rascunho'; }
 clear(): void { this.search=''; this.status=''; this.tipo=''; this.load(1); }
 load(page = 1): void {
  this.loading = true; this.error = ''; this.page = page;
  this.service.listAdminProperties({ search:this.search,status:this.status,tipo:this.tipo,page }).subscribe({
   next: response => { this.properties=response.results; this.count=response.count; this.next=!!response.next; this.previous=!!response.previous; this.loading=false; },
   error: () => { this.loading=false; this.error='Não foi possível carregar os imóveis. Seus cadastros não foram alterados.'; },
  });
 }
 numberValue(value: string | number): number { return Number(value || 0); }
 deleteSelected(): void {
  if (!this.selected) return;
  this.service.deleteProperty(this.selected.id).subscribe({next:()=>{ this.selected=null; this.notification.show({type:'success',text:'Imóvel inativado.'}); this.load(this.page); },error:()=>this.notification.show({type:'error',text:'Não foi possível inativar o imóvel.'})});
 }
}
