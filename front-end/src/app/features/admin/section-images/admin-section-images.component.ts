import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { SectionImage, SectionImageSection } from '@core/models/api.models';
import { SectionImageService } from '@core/services/section-image.service';
import { NotificationService } from '@core/services/notification.service';

@Component({
  selector: 'app-admin-section-images',
  standalone: true,
  imports: [FormsModule],
  template: `
  <div class="admin-page">
    <div class="admin-header"><h1>Imagens da página inicial</h1></div>
    <p class="muted">Gerencie as fotos dos carrosséis de Pontos Turísticos e Orla. Os slides são exibidos na ordem indicada.</p>
    <form class="card editor" (ngSubmit)="save()">
      <label class="field">Seção
        <select name="section" [(ngModel)]="section">
          <option value="tourism">Pontos Turísticos</option>
          <option value="investment">Orla, qualidade de vida e valorização</option>
        </select>
      </label>
      <label class="field">Legenda<input name="caption" [(ngModel)]="caption"></label>
      <label class="field">Ordem<input name="position" type="number" min="0" [(ngModel)]="position"></label>
      <label class="check"><input name="active" type="checkbox" [(ngModel)]="active"> Ativa</label>
      <label class="field">Imagem {{ editingId ? '(opcional ao editar)' : '(obrigatória)' }}
        <input type="file" accept="image/jpeg,image/png,image/webp" (change)="selectFile($event)">
      </label>
      <div class="actions">
        <button class="btn btn-primary" type="submit" [disabled]="saving || (!editingId && !file)">{{ saving ? 'Salvando…' : editingId ? 'Atualizar imagem' : 'Adicionar imagem' }}</button>
        <button class="btn btn-secondary" type="button" (click)="reset()">Cancelar</button>
      </div>
    </form>
    <div class="gallery">
      @for (item of images; track item.id) {
        <div class="card image-card">
          <img [src]="item.image" [alt]="item.caption || 'Imagem da seção'">
          <strong>{{ item.section === 'tourism' ? 'Pontos Turísticos' : 'Orla' }}</strong>
          <span>{{ item.caption || 'Sem legenda' }} · Ordem {{ item.position }} · {{ item.active ? 'Ativa' : 'Inativa' }}</span>
          <div class="actions">
            <button type="button" class="btn btn-secondary" (click)="edit(item)">Editar</button>
            <button type="button" class="btn btn-danger" (click)="remove(item)">Excluir</button>
          </div>
        </div>
      }
    </div>
  </div>`,
  styles: [`
    .editor{display:grid;gap:12px;padding:20px;margin:16px 0 24px;max-width:720px}
    .gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}
    .image-card{display:grid;gap:10px;padding:12px}
    .image-card img{width:100%;aspect-ratio:16/10;object-fit:cover;border-radius:6px}
    .actions{display:flex;gap:8px;flex-wrap:wrap}
    .check{display:flex;gap:8px;align-items:center}
  `]
})
export class AdminSectionImagesComponent implements OnInit {
  private readonly service = inject(SectionImageService);
  private readonly notification = inject(NotificationService);
  images: SectionImage[] = [];
  section: SectionImageSection = 'tourism';
  caption = ''; position = 0; active = true;
  editingId: number | null = null; file: File | null = null; saving = false;
  ngOnInit(): void { this.load(); }
  load(): void { this.service.list(true).subscribe({next: res => this.images = res.results}); }
  selectFile(e: Event): void { this.file = (e.target as HTMLInputElement).files?.[0] || null; }
  edit(item: SectionImage): void { this.editingId = item.id; this.section = item.section; this.caption = item.caption; this.position = item.position; this.active = item.active; this.file = null; }
  reset(): void { this.editingId = null; this.section = 'tourism'; this.caption = ''; this.position = 0; this.active = true; this.file = null; }
  save(): void {
    if (this.saving || (!this.editingId && !this.file)) return;
    const data = new FormData();
    data.append('section', this.section); data.append('caption', this.caption);
    data.append('position', String(this.position)); data.append('active', String(this.active));
    if (this.file) data.append('image', this.file);
    this.saving = true;
    const request = this.editingId ? this.service.update(this.editingId, data) : this.service.create(data);
    request.subscribe({
      next: () => { this.saving = false; this.reset(); this.load(); this.notification.show({type:'success',text:'Imagem salva.'}); },
      error: () => { this.saving = false; this.notification.show({type:'error',text:'Não foi possível salvar a imagem.'}); }
    });
  }
  remove(item: SectionImage): void {
    if (!confirm('Excluir esta imagem?')) return;
    this.service.remove(item.id).subscribe({next: () => this.load(),error: () => this.notification.show({type:'error',text:'Não foi possível excluir.'})});
  }
}
