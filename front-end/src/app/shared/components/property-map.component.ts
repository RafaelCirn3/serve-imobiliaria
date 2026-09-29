import { AfterViewInit, Component, ElementRef, EventEmitter, Input, OnChanges, OnDestroy, Output, ViewChild, ViewEncapsulation, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import type * as Leaflet from 'leaflet';
import { MapProperty } from '@core/models/api.models';
import { LocationService } from '@core/services/location.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-property-map', standalone: true, encapsulation: ViewEncapsulation.None,
  template: `
    <div class="serve-map-wrapper">
      <div #canvas class="serve-map-canvas" aria-label="Mapa de localização dos imóveis"></div>
      @if (error()) { <p role="alert">{{ error() }}</p> }
      @if (tilesFailed()) { <p role="status">O mapa de ruas está indisponível. Os imóveis continuam acessíveis pela lista.</p> }
      @if (!editable) { <p class="serve-map-caption">Marcadores indicam posições aproximadas, salvo localização confirmada no cadastro. Use a lista para navegar por todos os imóveis.</p> }
      @else { <p class="serve-map-caption">Arraste o marcador ou clique no mapa para ajustar a posição. Confira antes de publicar. © OpenStreetMap contributors.</p> }
    </div>
  `,
  styles: [`
    .serve-map-wrapper { min-width: 0; } .serve-map-canvas { height: 460px; width: 100%; border-radius: 12px; background: #29323b; z-index: 0; }
    .serve-map-caption, .serve-map-wrapper > p { font-size: .85rem; line-height: 1.5; color: #b8b8b8; }
    .serve-map-marker { border: 2px solid #fff; background: #111417; color: white; border-radius: 50%; text-align: center; line-height: 28px; font-size: 16px; box-shadow: 0 2px 8px #0008; }
    .serve-map-popup { max-width: 240px; display: grid; gap: 8px; } .serve-map-popup img { width: 100%; max-height: 130px; object-fit: cover; border-radius: 6px; }
    .serve-map-popup a { font-weight: 800; } .serve-map-popup p { margin: 0; } .leaflet-popup-content { color: #111417; }
    @media(max-width:560px) { .serve-map-canvas { height: 360px; } }
  `],
})
export class PropertyMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @Input() properties: MapProperty[] = [];
  @Input() editable = false;
  @Output() positionChanged = new EventEmitter<{ latitude: string; longitude: string }>();
  @ViewChild('canvas', { static: true }) canvas!: ElementRef<HTMLDivElement>;
  private readonly locations = inject(LocationService);
  private readonly router = inject(Router);
  private lib?: typeof Leaflet;
  private map?: Leaflet.Map;
  private markers?: Leaflet.FeatureGroup;
  private destroyed = false;
  readonly error = signal('');
  readonly tilesFailed = signal(false);

  async ngAfterViewInit(): Promise<void> {
    try {
      await import('leaflet');
      await import('leaflet.markercluster');
      const config = await firstValueFrom(this.locations.mapConfig());
      if (this.destroyed) return;
      const L = (window as unknown as { L: typeof Leaflet }).L;
      this.lib = L;
      this.map = L.map(this.canvas.nativeElement, { scrollWheelZoom: false, maxZoom: 19 }).setView([-7.1195, -34.845], 12);
      L.tileLayer(config.tile_url, { attribution: config.attribution, maxZoom: 19 }).on('tileerror', () => this.tilesFailed.set(true)).addTo(this.map);
      this.map.on('click', (event: Leaflet.LeafletMouseEvent) => {
        if (this.editable) this.emitPosition(event.latlng);
      });
      this.render();
    } catch {
      if (!this.destroyed) this.error.set('Não foi possível abrir o mapa. Consulte os imóveis pela lista.');
    }
  }

  ngOnChanges(): void { this.render(); }

  private render(): void {
    const L = this.lib, map = this.map;
    if (!L || !map) return;
    if (this.markers) map.removeLayer(this.markers);
    this.markers = this.editable ? L.featureGroup() : L.markerClusterGroup({ showCoverageOnHover: false });
    const bounds: Leaflet.LatLngTuple[] = [];
    for (const property of this.properties) {
      if (property.latitude == null || property.longitude == null || property.latitude === '' || property.longitude === '') continue;
      const latitude = Number(property.latitude), longitude = Number(property.longitude);
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude) || Math.abs(latitude) > 90 || Math.abs(longitude) > 180) continue;
      const position: Leaflet.LatLngTuple = [latitude, longitude]; bounds.push(position);
      const marker = L.marker(position, { title: property.titulo, draggable: this.editable,
        icon: L.divIcon({ className: 'serve-map-marker', html: '⌂', iconSize: [32, 32], iconAnchor: [16, 16] }) });
      marker.bindPopup(this.popup(property));
      if (this.editable) marker.on('dragend', () => this.emitPosition(marker.getLatLng()));
      this.markers.addLayer(marker);
    }
    this.markers.addTo(map);
    if (bounds.length) map.fitBounds(L.latLngBounds(bounds), { padding: [30, 30], maxZoom: this.editable ? 17 : 16, animate: false });
    map.invalidateSize();
  }

  private popup(property: MapProperty): HTMLElement {
    const node = document.createElement('div'); node.className = 'serve-map-popup';
    const photo = property.foto || property.imagens?.find((image) => image.imagem_capa)?.imagem || property.imagens?.[0]?.imagem;
    if (photo && /^(https?:\/\/|\/)/.test(photo)) {
      const image = document.createElement('img'); image.src = photo; image.alt = property.titulo; node.appendChild(image);
    }
    const title = document.createElement('strong'); title.textContent = property.titulo; node.appendChild(title);
    const price = document.createElement('p'); price.textContent = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(property.valor)); node.appendChild(price);
    const location = document.createElement('p'); location.textContent = `${property.bairro} · ${property.cidade} — ${property.localizacao_exata ? 'Localização confirmada' : 'Localização aproximada'}`; node.appendChild(location);
    if (property.slug) {
      const link = document.createElement('a'); link.href = `/imoveis/${encodeURIComponent(property.slug)}`; link.textContent = 'Ver imóvel';
      link.addEventListener('click', (event) => { event.preventDefault(); this.router.navigate(['/imoveis', property.slug]); }); node.appendChild(link);
    }
    return node;
  }
  private emitPosition(position: Leaflet.LatLng): void {
    this.positionChanged.emit({ latitude: position.lat.toFixed(7), longitude: position.lng.toFixed(7) });
  }
  ngOnDestroy(): void { this.destroyed = true; this.map?.remove(); }
}
