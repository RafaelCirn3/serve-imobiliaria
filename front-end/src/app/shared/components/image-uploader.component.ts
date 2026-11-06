import { Component, EventEmitter, Input, OnChanges, OnDestroy, Output } from '@angular/core';
import { PropertyImage } from '@core/models/api.models';

@Component({
  selector: 'app-image-uploader', standalone: true,
  template: `
    <div class="uploader card">
      <label class="drop">
        <input type="file" multiple accept="image/*,.heic,.heif" aria-label="Selecionar imagens do imóvel" [disabled]="busy" (change)="onSelect($event)">
        <span>Selecionar imagens</span>
        <small>Adicione fotos em etapas. Até 20 fotos e 10 MB por envio.</small>
      </label>
      @if (error) { <p role="alert">{{ error }}</p> }
      @if (files.length) {
        <p role="status">{{ files.length }} foto(s) selecionada(s), aguardando envio.</p>
        <div class="grid">
          @for (preview of previews; track preview.url; let index = $index) {
            <figure>
              @if (!preview.heic) { <img [src]="preview.url" [alt]="preview.name"> }
              <figcaption><span>{{ preview.name }}</span><button class="btn btn-secondary" type="button" [disabled]="busy" (click)="removePending(index)">Remover</button></figcaption>
            </figure>
          }
        </div>
      }
      @if (images.length) {
        <div class="grid">
          @for (image of images; track image.id) {
            <figure><img [src]="image.imagem" [alt]="image.legenda || 'Imagem do imóvel'">
              <figcaption><button class="btn btn-secondary" type="button" [disabled]="busy" (click)="makeCover.emit(image)">{{ image.imagem_capa ? 'Capa atual' : 'Definir capa' }}</button><button class="btn btn-danger" type="button" [disabled]="busy" (click)="remove.emit(image)">Excluir</button></figcaption>
            </figure>
          }
        </div>
      }
      @if (files.length && !deferUpload) { <button class="btn btn-primary" type="button" [disabled]="busy" (click)="upload.emit(files)">{{ busy ? 'Enviando…' : 'Enviar fotos selecionadas' }}</button> }
    </div>
  `,
  styles: [`
    .uploader { display: grid; gap: 16px; padding: 18px; min-width: 0; }
    .drop { position: relative; display: grid; place-items: center; text-align: center; gap: 8px; min-height: 140px; padding: 16px; border: 1px dashed #ffffff70; border-radius: 8px; background: #ffffff0d; color: white; }
    input { position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
    .drop:focus-within { outline: 2px solid white; outline-offset: 3px; }
    small { color: #b8b8b8; } p[role=alert] { color: #ffb4b4; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 12px; }
    img { width: 100%; aspect-ratio: 1.25; object-fit: cover; border-radius: 8px; } figure { margin: 0; min-width: 0; }
    figcaption { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; } span { overflow-wrap: anywhere; }
  `],
})
export class ImageUploaderComponent implements OnChanges, OnDestroy {
  @Input() images: PropertyImage[] = [];
  @Input() files: File[] = [];
  @Input() deferUpload = false;
  @Input() busy = false;
  @Output() selectionChanged = new EventEmitter<File[]>();
  @Output() upload = new EventEmitter<File[]>();
  @Output() remove = new EventEmitter<PropertyImage>();
  @Output() makeCover = new EventEmitter<PropertyImage>();
  previews: { url: string; name: string; heic: boolean }[] = [];
  error = '';

  ngOnChanges(): void { this.updatePreviews(); }
  onSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    const incoming = Array.from(input.files || []);
    input.value = '';
    if (!incoming.length) return;
    const files = [...this.files];
    for (const file of incoming) {
      if (!files.some(item => item.name === file.name && item.size === file.size && item.lastModified === file.lastModified)) files.push(file);
    }
    if (files.length > 20 || files.reduce((total, file) => total + file.size, 0) > 10 * 1024 * 1024) {
      this.error = 'Selecione até 20 fotos, somando no máximo 10 MB. As fotos anteriores foram mantidas.'; return;
    }
    this.error = '';
    this.files = files;
    this.selectionChanged.emit(files);
    this.updatePreviews();
  }
  removePending(index: number): void {
    this.files = this.files.filter((_, item) => item !== index);
    this.selectionChanged.emit(this.files);
    this.error = '';
    this.updatePreviews();
  }
  private updatePreviews(): void {
    this.revoke();
    this.previews = this.files.map(file => ({ url: URL.createObjectURL(file), name: file.name, heic: /heic|heif/i.test(file.type + file.name) }));
  }
  private revoke(): void { this.previews.forEach(preview => URL.revokeObjectURL(preview.url)); }
  ngOnDestroy(): void { this.revoke(); }
}
