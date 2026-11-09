import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Lead, Property } from '@core/models/api.models';
import { LeadService } from '@core/services/lead.service';
import { PropertyService } from '@core/services/property.service';
import { PhotoComponent } from '@shared/components/photo.component';
@Component({
 selector:'app-dashboard',standalone:true,imports:[DatePipe,RouterLink,PhotoComponent],
 template:`<div class="admin-page">
   <div class="admin-header"><div><span class="admin-eyebrow">VISÃO GERAL</span><h1>Seu painel de imóveis</h1><p class="muted">Organize os anúncios e acompanhe os próximos atendimentos.</p></div><a class="btn btn-primary" routerLink="/admin/imoveis/novo">+ Novo imóvel</a></div>
   @if (error) { <p class="admin-notice error" role="alert">{{ error }} <button class="btn btn-secondary" (click)="load()">Tentar novamente</button></p> }
   <div class="metrics"><article class="card metric"><span>Imóveis cadastrados</span><strong>{{ stats?.total ?? '—' }}</strong><a routerLink="/admin/imoveis">Ver portfólio →</a></article><article class="card metric"><span>Publicados no site</span><strong>{{ stats?.publicados ?? '—' }}</strong><small>Disponíveis para os visitantes</small></article><article class="card metric"><span>Rascunhos</span><strong>{{ stats?.rascunhos ?? '—' }}</strong><small>Cadastros para continuar</small></article><article class="card metric"><span>Contatos recebidos</span><strong>{{ stats?.leads ?? '—' }}</strong><a routerLink="/admin/leads">Abrir atendimentos →</a></article></div>
   @if (stats?.sem_fotos) { <div class="admin-notice attention"><strong>{{ stats?.sem_fotos }} imóvel(is) sem fotos</strong><span>Uma boa apresentação começa pelas imagens.</span><a routerLink="/admin/imoveis">Revisar portfólio →</a></div> }
   <div class="columns"><section class="card panel"><div class="panel-heading"><h2>Imóveis recentes</h2><a routerLink="/admin/imoveis">Ver todos →</a></div>@for (property of properties.slice(0,5);track property.id) { <a class="recent-property" [routerLink]="['/admin/imoveis',property.id,'editar']"><app-photo [src]="cover(property)" [alt]="property.titulo" [eager]="true"/><div><strong>{{ property.titulo }}</strong><span>{{ property.bairro }} · {{ property.cidade }}</span><small class="admin-badge" [attr.data-status]="property.status">{{ property.status === 'publicado' ? 'Publicado' : property.status === 'rascunho' ? 'Rascunho' : property.status }}</small></div><span aria-hidden="true">→</span></a> } @empty { <div class="admin-empty">Seu próximo imóvel começa aqui.<br><a class="btn btn-secondary" routerLink="/admin/imoveis/novo">Cadastrar primeiro imóvel</a></div> }</section>
   <section class="card panel"><div class="panel-heading"><h2>Últimos contatos</h2><a routerLink="/admin/leads">Ver todos →</a></div>@for (lead of leads.slice(0,5);track lead.id) { <a class="recent-lead" routerLink="/admin/leads"><span class="avatar">{{ lead.nome.slice(0,1).toUpperCase() }}</span><div><strong>{{ lead.nome }}</strong><span>{{ lead.telefone }}</span><small>{{ lead.criado_em | date:'dd/MM/yyyy HH:mm' }}</small></div><span aria-hidden="true">→</span></a> } @empty { <p class="admin-empty">Os contatos recebidos pelo site aparecerão aqui.</p> }</section></div>
  </div>`,
 styles:[`.metrics {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}.metric{padding:22px;display:grid;gap:12px}.metric>span{font-size:13px;color:#65717c}.metric>strong{font-size:36px;letter-spacing:-.04em}.metric a,.metric small{font-size:12px;color:#5c6874}.columns{display:grid;grid-template-columns:1.3fr 1fr;gap:24px}.panel{padding:24px}.panel-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}.panel-heading h2{font-size:17px;margin:0}.panel-heading a{font-size:12px;color:#68737c}.recent-property,.recent-lead{display:flex;align-items:center;gap:14px;padding:16px 0;border-top:1px solid #edf0f2}.recent-property app-photo{flex:0 0 96px;width:96px;height:72px;border-radius:8px}.recent-property>div,.recent-lead>div{display:grid;gap:5px;flex:1;min-width:0}.recent-property strong,.recent-lead strong{font-size:13px;line-height:1.4}.recent-property span,.recent-lead span,.recent-lead small{font-size:12px;color:#68737c}.avatar{width:40px;height:40px;display:grid;place-items:center;background:#edf1f3;border-radius:50%}.recent-property .admin-badge{justify-self:start;font-size:10px}@media(max-width:1100px){.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.columns{grid-template-columns:1fr}}@media(max-width:480px){.metric{padding:16px}.panel{padding:16px}.recent-property app-photo{width:76px;flex-basis:76px;height:62px}}`],
})
export class DashboardComponent implements OnInit {
 private readonly service=inject(PropertyService);private readonly leadService=inject(LeadService);
 stats: {total:number;publicados:number;rascunhos:number;sem_fotos:number;leads:number}|null=null;
 properties:Property[]=[];leads:Lead[]=[];error='';
 cover(property:Property):string {return property.imagens.find(image=>image.imagem_capa)?.imagem || property.imagens[0]?.imagem || '';}
 ngOnInit():void{this.load();}
 load():void{
  this.error='';
  this.service.adminSummary().subscribe({next:stats=>this.stats=stats,error:()=>this.error='Não foi possível carregar o resumo.'});
  this.service.listAdminProperties({ordering:'-criado_em'}).subscribe({next:r=>this.properties=r.results,error:()=>this.error='Não foi possível carregar os imóveis recentes.'});
  this.leadService.listAdminLeads().subscribe({next:r=>this.leads=r.results,error:()=>this.error='Não foi possível carregar os contatos.'});
 }
}
