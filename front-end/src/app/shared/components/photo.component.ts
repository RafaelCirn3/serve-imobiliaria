import { Component, Input, OnChanges } from '@angular/core';
import { mediaUrl } from '@core/services/media-url';

@Component({
  selector: 'app-photo', standalone: true, host: { '[class.natural]': 'natural' },
  template: `
    @if (url && !failed) {
      <img [attr.draggable]="natural ? false : null" [src]="url" [alt]="alt" [attr.loading]="eager ? 'eager' : 'lazy'" [style.object-fit]="fit" [class.loaded]="loaded" (load)="loaded = true" (error)="failed = true">
      @if (!loaded) { <span class="loading" aria-hidden="true"></span> }
    } @else {
      <span class="empty" role="img" [attr.aria-label]="url ? 'Foto indisponível' : 'Imóvel sem fotos'">
        <svg viewBox="0 0 48 48" aria-hidden="true"><rect x="6" y="10" width="36" height="28" rx="5"/><circle cx="17" cy="20" r="3"/><path d="m9 34 10-9 7 6 5-5 8 8"/></svg>
        <span>{{ url ? 'Foto indisponível' : 'Sem fotos disponíveis' }}</span>
      </span>
    }
  `,
  styles: [`
    :host { display: block; position: relative; width: 100%; height: 100%; overflow: hidden; background: #e9edf0; color: #5d6973; }
    :host(.natural) { width: fit-content; max-width: 100%; height: auto; background: transparent; justify-self: center; }
    :host(.natural) img { width: auto; height: auto; max-width: 100%; max-height: min(620px, 80dvh); border-radius: 8px; }
    img { display: block; width: 100%; height: 100%; opacity: 0; transition: opacity .15s; } img.loaded { opacity: 1; }
    .loading { position: absolute; inset: 0; background: linear-gradient(100deg,#e9edf0,#f8fafb,#e9edf0); background-size: 200% 100%; animation: shimmer 1.5s linear infinite; }
    .empty { width: 100%; height: 100%; min-height: 60px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; padding: 12px; text-align: center; font-size: 12px; font-weight: 600; }
    svg { width: 38px; height: 38px; fill: none; stroke: currentColor; stroke-width: 1.5; }
    @keyframes shimmer { to { background-position: -200% 0; } }
    @media(prefers-reduced-motion:reduce) { .loading { animation: none; } }
  `],
})
export class PhotoComponent implements OnChanges {
  @Input() src: string | null | undefined = '';
  @Input() alt = 'Foto do imóvel';
  @Input() eager = false;
  @Input() natural = false;
  @Input() fit = 'cover';
  url = ''; loaded = false; failed = false;
  ngOnChanges(): void { const next = mediaUrl(this.src); if (next !== this.url) { this.url = next; this.loaded = false; this.failed = false; } }
}
