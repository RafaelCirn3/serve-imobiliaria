import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { PropertyImage, PropertyPayload, Region } from '@core/models/api.models';
import { PROPERTY_TYPES } from '@core/models/property-options';
import { NotificationService } from '@core/services/notification.service';
import { PropertyService } from '@core/services/property.service';
import { RegionService } from '@core/services/region.service';
import { ImageUploaderComponent } from '@shared/components/image-uploader.component';
import { AddressEditorComponent } from '@shared/components/address-editor.component';
import { PropertyMapComponent } from '@shared/components/property-map.component';
import { LocationService } from '@core/services/location.service';
import { MapProperty } from '@core/models/api.models';

@Component({
  selector: 'app-property-form',
  standalone: true,
  imports: [ReactiveFormsModule, ImageUploaderComponent, AddressEditorComponent, PropertyMapComponent],
  template: `
    <div class="admin-page">
      <div class="admin-header">
        <div>
          <h1>{{ propertyId ? 'Editar imóvel' : 'Novo imóvel' }}</h1>
          <p class="muted">Organize dados, localização, características, fotos e SEO.</p>
        </div>
        <button class="btn btn-primary" type="button" (click)="save()">Salvar</button>
      </div>

      <nav class="tabs">
        @for (item of tabs; track item.id) {
          <button type="button" [class.active]="tab === item.id" (click)="tab = item.id">{{ item.label }}</button>
        }
      </nav>

      <form class="card form-card" [formGroup]="form">
        @if (tab === 'basic') {
          <div class="form-grid">
            <label class="field">Titulo<input formControlName="titulo"></label>
            <label class="field">Valor<input type="number" formControlName="valor"></label>
            <label class="field full">Descrição<textarea formControlName="descricao"></textarea></label>
            <label class="field">Tipo<select formControlName="tipo">
              @for (type of propertyTypes; track type.value) { <option [value]="type.value">{{ type.label }}</option> }
            </select></label>
            <label class="field">Finalidade<select formControlName="finalidade"><option value="venda">Venda</option><option value="aluguel">Aluguel</option></select></label>
            <label class="field">Condomínio<input type="number" formControlName="valor_condominio"></label>
            <label class="field">IPTU<input type="number" formControlName="valor_iptu"></label>
          </div>
        }

        @if (tab === 'location') {
          <div class="form-grid">
            <label class="field full">Região
              <select formControlName="regiao" (change)="applyRegion($event)">
                <option [ngValue]="null">Sem região vinculada</option>
                @for (region of regions; track region.id) {
                  <option [value]="region.id">{{ region.nome }} · {{ region.cidade }}</option>
                }
              </select>
            </label>
            <app-address-editor [form]="form" listId="admin-address" />
            <label class="field full">Endereço anterior / referência<input formControlName="endereco"></label>
            <label class="field">Latitude<input formControlName="latitude"></label>
            <label class="field">Longitude<input formControlName="longitude"></label>
            <button type="button" class="btn btn-secondary" [disabled]="geocoding" (click)="geocode()">{{ geocoding ? 'Localizando…' : 'Localizar endereço no mapa' }}</button>
            <label class="check"><input type="checkbox" formControlName="localizacao_exata"> Publicar localização exata (posição conferida)</label>
            <p class="muted full">A posição é aproximada por padrão. Ao publicar a localização exata, número e complemento também ficam disponíveis ao público.</p>
            @if (mapPreview.length) { <div class="full"><app-property-map [properties]="mapPreview" [editable]="true" (positionChanged)="movePosition($event)" /></div> }
          </div>
        }

        @if (tab === 'features') {
          <div class="form-grid">
            <label class="field">Área total (m²)<input type="number" min="0" step="0.01" formControlName="area_total"></label>
            <label class="field">Área privativa (m²)<input type="number" min="0" step="0.01" formControlName="area_privativa"></label>
            @if (form.controls.tipo.value === 'terreno') {
              <p class="muted full">Para áreas e terrenos, informe a metragem no campo Área total.</p>
            }
            <label class="field">Quartos<input type="number" formControlName="quartos"></label>
            <label class="field">Suítes<input type="number" formControlName="suites"></label>
            <label class="field">Banheiros<input type="number" formControlName="banheiros"></label>
            <label class="field">Vagas<input type="number" formControlName="vagas"></label>
            <label class="check"><input type="checkbox" formControlName="aceita_financiamento"> Aceita financiamento</label>
            <label class="check"><input type="checkbox" formControlName="mobiliado"> Mobiliado</label>
            <label class="check"><input type="checkbox" formControlName="possui_piscina"> Piscina</label>
            <label class="check"><input type="checkbox" formControlName="possui_academia"> Academia</label>
            <label class="check"><input type="checkbox" formControlName="possui_elevador"> Elevador</label>
            <label class="check"><input type="checkbox" formControlName="possui_area_gourmet"> Área gourmet</label>
          </div>
        }

        @if (tab === 'photos') {
          @if (propertyId) {
            <app-image-uploader [images]="images" (upload)="uploadImages($event)" (remove)="deleteImage($event)" (makeCover)="makeCover($event)" />
          } @else {
            <p class="muted">Salve o imóvel antes de enviar fotos.</p>
          }
        }

        @if (tab === 'seo') {
          <div class="form-grid">
            <label class="field">Status<select formControlName="status"><option value="rascunho">Rascunho</option><option value="publicado">Publicado</option><option value="vendido">Vendido</option><option value="alugado">Alugado</option><option value="inativo">Inativo</option></select></label>
            <label class="check"><input type="checkbox" formControlName="destaque"> Imóvel em destaque</label>
            <label class="field full">Titulo SEO<input formControlName="titulo_seo"></label>
            <label class="field full">Descrição SEO<textarea formControlName="descricao_seo"></textarea></label>
          </div>
        }
      </form>
    </div>
  `,
  styles: [`
    .tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .tabs button {
      border: 1px solid #30363d;
      border-radius: 8px;
      background: #181c20;
      color: #b8b8b8;
      padding: 10px 12px;
      font-weight: 800;
    }

    .tabs button.active {
      border-color: rgba(255, 255, 255, 0.42);
      color: #ffffff;
    }

    .form-card {
      padding: 20px;
    }

    .full {
      grid-column: 1 / -1;
    }

    .check {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #d8d8d8;
      font-weight: 800;
    }
  `],
})
export class PropertyFormComponent implements OnInit {
  readonly propertyTypes = PROPERTY_TYPES;
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly propertiesService = inject(PropertyService);
  private readonly regionsService = inject(RegionService);
  private readonly notification = inject(NotificationService);
  private readonly locations = inject(LocationService);
  private readonly destroyRef = inject(DestroyRef);
  geocoding = false;
  private previewKey = '';
  private previewProperties: MapProperty[] = [];

  propertyId: string | null = null;
  tab = 'basic';
  images: PropertyImage[] = [];
  regions: Region[] = [];
  readonly tabs = [
    { id: 'basic', label: 'Informações básicas' },
    { id: 'location', label: 'Localização' },
    { id: 'features', label: 'Características' },
    { id: 'photos', label: 'Fotos' },
    { id: 'seo', label: 'SEO/Publicação' },
  ];

  readonly form = this.fb.nonNullable.group({
    titulo: ['', Validators.required],
    descricao: ['', Validators.required],
    tipo: ['apartamento'],
    finalidade: ['venda'],
    status: ['rascunho'],
    destaque: [false],
    valor: [0, Validators.required],
    valor_condominio: [null as number | null],
    valor_iptu: [null as number | null],
    regiao: [null as number | null],
    cidade: ['João Pessoa', Validators.required],
    bairro: ['', Validators.required],
    endereco: [''],
    uf: ['PB'], logradouro: [''], numero: [''], complemento: [''],
    cep: [''],
    latitude: [''],
    longitude: [''],
    localizacao_exata: [false],
    area_total: [null as number | null],
    area_privativa: [null as number | null],
    quartos: [0],
    suites: [0],
    banheiros: [0],
    vagas: [0],
    aceita_financiamento: [false],
    mobiliado: [false],
    possui_piscina: [false],
    possui_academia: [false],
    possui_elevador: [false],
    possui_area_gourmet: [false],
    titulo_seo: [''],
    descricao_seo: [''],
  });

  ngOnInit(): void {
    this.regionsService.listRegions(true).subscribe((response) => (this.regions = response.results));
    this.propertyId = this.route.snapshot.paramMap.get('id');
    if (this.propertyId) {
      this.propertiesService.getAdminProperty(this.propertyId).subscribe((property) => {
        this.form.patchValue(property as never);
        this.images = property.imagens;
      });
    }
  }

  applyRegion(event: Event): void {
    const regionId = Number((event.target as HTMLSelectElement).value);
    const region = this.regions.find((item) => item.id === regionId);
    if (!region) {
      return;
    }
    this.form.patchValue({
      regiao: region.id,
      cidade: region.cidade,
      bairro: region.nome,
    });
  }

  save(): void {
    if (this.form.invalid) {
      this.notification.show({ type: 'error', text: 'Preencha os campos obrigatorios.' });
      return;
    }

    const values = this.form.getRawValue();
    const payload = { ...values, latitude: values.latitude || null, longitude: values.longitude || null } as PropertyPayload;
    const request = this.propertyId
      ? this.propertiesService.updateProperty(this.propertyId, payload)
      : this.propertiesService.createProperty(payload);

    request.subscribe({
      next: (property) => {
        this.notification.show({ type: 'success', text: 'Imóvel salvo.' });
        if (!this.propertyId) {
          this.router.navigate(['/admin/imoveis', property.id, 'editar']);
        } else {
          this.images = property.imagens;
        }
      },
      error: (response) => this.notification.show({ type: 'error', text: response.status === 400 ? 'Revise cidade, UF, CEP, região e coordenadas antes de salvar.' : 'Não foi possível salvar o imóvel.' }),
    });
  }

  uploadImages(files: File[]): void {
    if (!this.propertyId) {
      return;
    }
    this.propertiesService.uploadPropertyImages(this.propertyId, files).subscribe({
      next: () => {
        this.notification.show({ type: 'success', text: 'Fotos enviadas.' });
        this.reloadProperty();
      },
      error: () => this.notification.show({ type: 'error', text: 'Falha no upload das fotos.' }),
    });
  }

  get mapPreview(): MapProperty[] {
    const values = this.form.getRawValue();
    const key = JSON.stringify([values.latitude, values.longitude, values.titulo, values.valor, values.cidade, values.bairro, values.localizacao_exata]);
    if (this.previewKey === key) return this.previewProperties;
    this.previewKey = key;
    if (values.latitude == null || values.longitude == null || values.latitude === '' || values.longitude === '') { this.previewProperties = []; return this.previewProperties; }
    this.previewProperties = [{ id: 0, titulo: values.titulo || 'Prévia da localização', slug: '', valor: values.valor,
      cidade: values.cidade, bairro: values.bairro, latitude: values.latitude, longitude: values.longitude,
      localizacao_exata: values.localizacao_exata }];
    return this.previewProperties;
  }

  movePosition(position: { latitude: string; longitude: string }): void {
    this.form.patchValue({ ...position, localizacao_exata: false });
  }

  geocode(): void {
    if (this.geocoding) return;
    const { cidade, bairro, logradouro, numero, uf } = this.form.getRawValue();
    if (!logradouro || !cidade || uf !== 'PB') {
      this.notification.show({ type: 'error', text: 'Informe a cidade, UF PB e a rua antes de localizar.' }); return;
    }
    this.geocoding = true;
    const address = { cidade, bairro, logradouro, numero, uf };
    const coordinates = { latitude: this.form.controls.latitude.value, longitude: this.form.controls.longitude.value };
    this.locations.geocode({ cidade, bairro, logradouro, numero }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (result) => {
        this.geocoding = false;
        const current = this.form.getRawValue();
        if (Object.entries({ ...address, ...coordinates }).some(([field, value]) => current[field as keyof typeof current] !== value)) {
          this.notification.show({ type: 'error', text: 'O endereço ou as coordenadas foram alterados. Consulte a localização novamente.' });
          return;
        }
        this.form.patchValue({ latitude: result.latitude.toFixed(7), longitude: result.longitude.toFixed(7), localizacao_exata: false });
        this.notification.show({ type: 'success', text: 'Posição sugerida. Confira no mapa e salve o imóvel.' });
      },
      error: (response) => { this.geocoding = false; this.notification.show({ type: 'error', text: response.status === 429 ? 'Aguarde alguns segundos antes de consultar novamente.' : 'Não foi possível localizar. Você pode informar as coordenadas manualmente.' }); },
    });
  }

  deleteImage(image: PropertyImage): void {
    if (!this.propertyId) {
      return;
    }
    this.propertiesService.deletePropertyImage(this.propertyId, image.id).subscribe(() => {
      this.images = this.images.filter((item) => item.id !== image.id);
    });
  }

  makeCover(image: PropertyImage): void {
    if (!this.propertyId) {
      return;
    }
    this.propertiesService.updatePropertyImage(this.propertyId, image.id, { imagem_capa: true }).subscribe(() => this.reloadProperty());
  }

  private reloadProperty(): void {
    if (!this.propertyId) {
      return;
    }
    this.propertiesService.getAdminProperty(this.propertyId).subscribe((property) => (this.images = property.imagens));
  }
}


