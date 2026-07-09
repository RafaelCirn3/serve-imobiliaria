import { Component, EventEmitter, Input, Output } from '@angular/core';
import { PropertyImage } from '@core/models/api.models';

@Component({
  selector: 'app-image-uploader',
  standalone: true,
  template: `
    <div class="uploader card">
      <label class="drop">
        <input type="file" multiple accept="image/*" (change)="onSelect($event)">
        <span>Selecionar imagens</span>
        <small>Upload múltiplo com preview local</small>
      </label>
      @if (previews.length) {
        <div class="grid">
          @for (preview of previews; track preview) {
            <img [src]="preview" alt="Preview da imagem">
          }
        </div>
      }
      @if (images.length) {
        <div class="grid">
          @for (image of images; track image.id) {
            <figure>
              <img [src]="image.imagem" [alt]="image.legenda || 'Imagem do imóvel'">
              <figcaption>
                <button class="btn btn-secondary" type="button" (click)="makeCover.emit(image)">Capa</button>
                <button class="btn btn-danger" type="button" (click)="remove.emit(image)">Excluir</button>
              </figcaption>
            </figure>
          }
        </div>
      }
      @if (selected.length) {
        <button class="btn btn-primary" type="button" (click)="upload.emit(selected)">Enviar {{ selected.length }} imagem(ns)</button>
      }
    </div>
  `,
  styles: [`
    .uploader {
      display: grid;
      gap: 16px;
      padding: 18px;
    }

    .drop {
      display: grid;
      place-items: center;
      min-height: 160px;
      border: 1px dashed rgba(255, 255, 255, 0.42);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.05);
      color: #ffffff;
      font-weight: 900;
    }

    input {
      display: none;
    }

    small {
      color: #b8b8b8;
      font-weight: 600;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 12px;
    }

    img {
      width: 100%;
      aspect-ratio: 1.25;
      object-fit: cover;
      border-radius: 8px;
    }

    figure {
      margin: 0;
    }

    figcaption {
      display: flex;
      gap: 8px;
      margin-top: 8px;
    }
  `],
})
export class ImageUploaderComponent {
  @Input() images: PropertyImage[] = [];
  @Output() upload = new EventEmitter<File[]>();
  @Output() remove = new EventEmitter<PropertyImage>();
  @Output() makeCover = new EventEmitter<PropertyImage>();

  selected: File[] = [];
  previews: string[] = [];

  onSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selected = Array.from(input.files || []);
    this.previews = this.selected.map((file) => URL.createObjectURL(file));
  }
}


