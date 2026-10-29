import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HomeContent } from '@core/models/api.models';
import { HomeContentService } from '@core/services/home-content.service';
import { NotificationService } from '@core/services/notification.service';

@Component({
  selector: 'app-admin-home-content',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="admin-page">
      <div class="admin-header"><h1>Textos da página inicial</h1></div>
      @if (content) {
        <form class="card editor" (ngSubmit)="save()">
          @for (field of fields; track field.key) {
            <label class="field">{{ field.label }}
              @if (field.long) {
                <textarea rows="3" [name]="field.key" [(ngModel)]="content[field.key]"></textarea>
              } @else {
                <input [name]="field.key" [(ngModel)]="content[field.key]">
              }
            </label>
          }
          <button class="btn btn-primary" [disabled]="saving" type="submit">{{ saving ? 'Salvando…' : 'Salvar textos' }}</button>
        </form>
      }
    </div>
  `,
  styles: [`.editor { display:grid; gap:16px; padding:22px; max-width:850px; } textarea { min-height:90px; }`],
})
export class AdminHomeContentComponent implements OnInit {
  private readonly service = inject(HomeContentService);
  private readonly notification = inject(NotificationService);
  content: HomeContent | null = null;
  saving = false;
  readonly fields: {key: keyof HomeContent; label: string; long?: boolean}[] = [
    {key:'hero_title',label:'Hero — título'}, {key:'hero_subtitle',label:'Hero — subtítulo',long:true},
    {key:'featured_label',label:'Destaques — etiqueta'}, {key:'featured_title',label:'Destaques — título'},
    {key:'regions_label',label:'Regiões — etiqueta'}, {key:'regions_title',label:'Regiões — título'},
    {key:'investment_label',label:'Investimento — etiqueta'}, {key:'investment_title',label:'Investimento — título'},
    {key:'investment_body',label:'Investimento — parágrafo 1',long:true}, {key:'investment_extra',label:'Investimento — parágrafo 2',long:true},
    {key:'owner_label',label:'Proprietários — etiqueta'}, {key:'owner_title',label:'Proprietários — título'},
    {key:'owner_body',label:'Proprietários — texto',long:true}, {key:'owner_button',label:'Proprietários — botão'},
  ];
  ngOnInit() { this.service.load().subscribe({next: v => this.content = v, error: () => this.notification.show({type:'error',text:'Não foi possível carregar os textos.'})}); }
  save() {
    if (!this.content || this.saving) return;
    this.saving = true;
    this.service.update(this.content).subscribe({
      next: v => { this.content = v; this.saving = false; this.notification.show({type:'success',text:'Textos atualizados.'}); },
      error: () => {this.saving = false; this.notification.show({type:'error',text:'Erro ao salvar os textos.'});}
    });
  }
}
