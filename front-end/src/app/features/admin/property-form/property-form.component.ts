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
          <p class="muted">Preencha os campos com *. Escolha Publicado na aba Publicação para exibir o imóvel no site.</p>
        </div>
        <button class="btn btn-primary" type="button" [disabled]="saving" (click)="save()">{{ saving ? "Salvando…" : "Salvar" }}</button>
      </div>

      <nav class="tabs">
        @for (item of tabs; track item.id) {
          <button type="button" [class.active]="tab === item.id" (click)="tab = item.id">{{ item.label }}{{ tabHasErrors(item.id) ? ' ⚠' : '' }}</button>
        }
      </nav>

      @if (draftRestored) { <p role="status">Rascunho recuperado neste navegador. Fotos precisam ser selecionadas novamente após recarregar a página. <button class="btn btn-secondary" type="button" (click)="discardDraft()">Descartar rascunho recuperado</button></p> }
      @if (errors.length) { <div class="error-summary" role="alert"><strong>Confira antes de salvar:</strong><ul>@for (error of errors; track $index) { <li><button type="button" (click)="showField(error.field)">{{ error.message }}</button></li> }</ul></div> }
      <form class="card form-card" [formGroup]="form" (ngSubmit)="save()">
        <fieldset [disabled]="saving">
        <div [hidden]="tab !== 'basic'">
          <div class="form-grid">
            <label class="field">Título *<input formControlName="titulo"></label>
            <label class="field">Valor *<input type="number" formControlName="valor"></label>
            <label class="field full">Descrição *<textarea formControlName="descricao"></textarea></label>
            <label class="field">Tipo<select formControlName="tipo">
              @for (type of propertyTypes; track type.value) { <option [value]="type.value">{{ type.label }}</option> }
            </select></label>
            <label class="field">Finalidade<select formControlName="finalidade"><option value="venda">Venda</option><option value="aluguel">Aluguel</option></select></label>
            <label class="field">Condomínio<input type="number" formControlName="valor_condominio"></label>
            <label class="field">IPTU<input type="number" formControlName="valor_iptu"></label>
          </div>
        </div>

        <div [hidden]="tab !== 'location'">
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
        </div>

        <div [hidden]="tab !== 'features'">
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
        </div>

        <div [hidden]="tab !== 'photos'">
          <p class="muted">{{ propertyId ? 'Adicione ou gerencie as imagens do imóvel.' : 'Fotos opcionais: selecione agora e elas serão enviadas ao salvar o imóvel.' }}</p>
          <app-image-uploader [files]="pendingImages" [busy]="saving" [images]="images" [deferUpload]="!propertyId" (selectionChanged)="stageImages($event)" (upload)="uploadImages($event)" (remove)="deleteImage($event)" (makeCover)="makeCover($event)" />
        </div>

        <div [hidden]="tab !== 'seo'">
          <p>Publicado exibe o imóvel no site. Rascunho guarda o cadastro para continuar depois. Marque Destaque para incluí-lo na vitrine inicial.</p>
          <div class="form-grid">
            <label class="field">Status<select formControlName="status"><option value="rascunho">Rascunho</option><option value="publicado">Publicado</option><option value="vendido">Vendido</option><option value="alugado">Alugado</option><option value="inativo">Inativo</option></select></label>
            <label class="check"><input type="checkbox" formControlName="destaque"> Imóvel em destaque</label>
            <label class="field full">Título para buscadores (opcional)<input formControlName="titulo_seo"></label>
            <label class="field full">Descrição para buscadores (opcional)<textarea formControlName="descricao_seo"></textarea></label>
          </div>
        </div>
        <p class="muted">{{ form.controls.status.value === 'publicado' ? 'Ao salvar, este imóvel ficará visível no site.' : 'Este imóvel não será exibido no site enquanto estiver como rascunho, vendido, alugado ou inativo.' }}</p>
        <button class="btn btn-primary" type="submit" [disabled]="saving">{{ saving ? 'Salvando…' : 'Salvar imóvel e fotos' }}</button>
        </fieldset>
      </form>
    </div>
  `,
  styles: [`
    fieldset { border: 0; padding: 0; margin: 0; min-width: 0; }
    [hidden] { display: none !important; }
    .error-summary { color: #ffb4b4; }
    .error-summary button { background: transparent; border: 0; color: inherit; text-align: left; text-decoration: underline; padding: 8px; }
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
  saving = false;
  pendingImages: File[] = [];
  private previewKey = '';
  private previewProperties: MapProperty[] = [];

  errors: { field: string; message: string }[] = [];
  draftRestored = false;
  private loadedValues: Record<string, unknown> = {};
  private draftKey = '';
  private readonly fieldLabels: Record<string, string> = {
    titulo: 'Título', descricao: 'Descrição', valor: 'Valor', valor_condominio: 'Condomínio', valor_iptu: 'IPTU',
    cidade: 'Cidade', bairro: 'Bairro', uf: 'UF', cep: 'CEP', regiao: 'Região', latitude: 'Latitude', longitude: 'Longitude',
    logradouro: 'Rua', numero: 'Número', complemento: 'Complemento', endereco: 'Referência',
    quartos: 'Quartos', suites: 'Suítes', banheiros: 'Banheiros', vagas: 'Vagas', area_total: 'Área total', area_privativa: 'Área privativa',
    status: 'Status', titulo_seo: 'Título para buscadores', descricao_seo: 'Descrição para buscadores',
  };
  private fieldTab(field: string): string {
    if (['cidade','bairro','uf','cep','regiao','latitude','longitude','logradouro','numero','complemento','endereco','localizacao_exata'].includes(field)) return 'location';
    if (['quartos','suites','banheiros','vagas','area_total','area_privativa'].includes(field)) return 'features';
    if (['status','destaque','titulo_seo','descricao_seo'].includes(field)) return 'seo';
    if (field === 'imagens') return 'photos';
    return 'basic';
  }
  tabHasErrors(tab: string): boolean { return this.errors.some(error => this.fieldTab(error.field) === tab); }
  showField(field: string): void {
    this.tab = this.fieldTab(field);
    setTimeout(() => document.querySelector<HTMLElement>(`[formControlName="${field}"]`)?.focus());
  }
  private restoreDraft(): void {
    this.loadedValues = this.form.getRawValue();
    try {
      const draft = sessionStorage.getItem(this.draftKey);
      if (draft) { this.form.patchValue(JSON.parse(draft)); this.draftRestored = true; }
    } catch { /* Storage may be unavailable in private browsing. */ }
    this.form.valueChanges.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      try { sessionStorage.setItem(this.draftKey, JSON.stringify(this.form.getRawValue())); } catch { /* Keep in-memory values. */ }
    });
  }
  discardDraft(): void {
    this.form.patchValue(this.loadedValues);
    this.draftRestored = false;
    this.clearDraft();
  }
  private clearDraft(): void {
    try { sessionStorage.removeItem(this.draftKey); } catch { /* Storage unavailable. */ }
    this.draftRestored = false;
    this.loadedValues = this.form.getRawValue();
    if (this.propertyId) this.draftKey = this.draftKey.replace(/[^:]+$/, this.propertyId);
  }
  propertyId: string | null = null;
  tab = 'basic';
  images: PropertyImage[] = [];
  regions: Region[] = [];
  readonly tabs = [
    { id: 'basic', label: 'Informações básicas' },
    { id: 'location', label: 'Localização' },
    { id: 'features', label: 'Características' },
    { id: 'photos', label: 'Fotos' },
    { id: 'seo', label: 'Publicação' },
  ];

  readonly form = this.fb.nonNullable.group({
    titulo: ['', [Validators.required, Validators.pattern(/\S/), Validators.maxLength(180)]],
    descricao: ['', [Validators.required, Validators.pattern(/\S/)]],
    tipo: ['apartamento'],
    finalidade: ['venda'],
    status: ['rascunho'],
    destaque: [false],
    valor: [0, [Validators.required, Validators.min(0)]],
    valor_condominio: [null as number | null, Validators.min(0)],
    valor_iptu: [null as number | null, Validators.min(0)],
    regiao: [null as number | null],
    cidade: ['João Pessoa', Validators.required],
    bairro: ['', [Validators.required, Validators.pattern(/\S/), Validators.maxLength(120)]],
    endereco: [''],
    uf: ['PB'], logradouro: [''], numero: [''], complemento: [''],
    cep: [''],
    latitude: [''],
    longitude: [''],
    localizacao_exata: [false],
    area_total: [null as number | null, Validators.min(0)],
    area_privativa: [null as number | null, Validators.min(0)],
    quartos: [0, [Validators.min(0), Validators.max(32767), Validators.pattern(/^\d+$/)]],
    suites: [0, [Validators.min(0), Validators.max(32767), Validators.pattern(/^\d+$/)]],
    banheiros: [0, [Validators.min(0), Validators.max(32767), Validators.pattern(/^\d+$/)]],
    vagas: [0, [Validators.min(0), Validators.max(32767), Validators.pattern(/^\d+$/)]],
    aceita_financiamento: [false],
    mobiliado: [false],
    possui_piscina: [false],
    possui_academia: [false],
    possui_elevador: [false],
    possui_area_gourmet: [false],
    titulo_seo: ['', Validators.maxLength(180)],
    descricao_seo: ['', Validators.maxLength(255)],
  });

  ngOnInit(): void {
    this.regionsService.listRegions(true).subscribe((response) => (this.regions = response.results));
    this.propertyId = this.route.snapshot.paramMap.get('id');
    let owner = 'admin';
    try { owner = sessionStorage.getItem('serve-draft-owner') || owner; } catch { /* Storage unavailable. */ }
    this.draftKey = `serve-property-draft:${owner}:${this.propertyId || 'new'}`;
    if (this.propertyId) {
      this.propertiesService.getAdminProperty(this.propertyId).subscribe((property) => {
        this.form.patchValue(property as never);
        this.images = property.imagens;
        this.restoreDraft();
      });
    } else { this.restoreDraft(); }
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
    if (this.saving) return;
    this.errors = [];
    this.form.markAllAsTouched();
    if (this.form.invalid) {
      for (const [field, control] of Object.entries(this.form.controls)) {
        if (control.invalid) this.errors.push({ field, message: `${this.fieldLabels[field] || field}: ${control.hasError('required') ? 'preencha este campo.' : 'informe um valor válido, respeitando os limites do campo.'}` });
      }
      this.showField(this.errors[0].field);
      return;
    }

    const values = this.form.getRawValue();
    const payload = { ...values, latitude: values.latitude || null, longitude: values.longitude || null,
      quartos: values.quartos ?? 0, suites: values.suites ?? 0, banheiros: values.banheiros ?? 0, vagas: values.vagas ?? 0,
    } as PropertyPayload;
    const request = this.propertyId
      ? this.propertiesService.updateProperty(this.propertyId, payload)
      : this.propertiesService.createProperty(payload);

    this.saving = true;
    request.subscribe({
      next: (property) => {
        this.propertyId = String(property.id);
        this.images = property.imagens;
        if (this.pendingImages.length) {
          const files = [...this.pendingImages];
          this.propertiesService.uploadPropertyImages(property.id, files).subscribe({
            next: () => {
              this.pendingImages = [];
              this.clearDraft();
              this.saving = false;
              this.notification.show({ type: 'success', text: 'Imóvel e fotos salvos.' });
              this.router.navigate(['/admin/imoveis', property.id, 'editar']);
              this.reloadProperty();
            },
            error: () => {
              this.saving = false;
              this.notification.show({ type: 'error', text: 'Imóvel salvo, mas as fotos não foram enviadas. Tente enviá-las novamente.' });
              this.tab = 'photos';
            },
          });
        } else {
          this.saving = false;
          this.clearDraft();
          this.notification.show({ type: 'success', text: 'Imóvel salvo.' });
          this.router.navigate(['/admin/imoveis', property.id, 'editar']);
        }
      },
      error: (response) => {
        this.saving = false;
        if (response.status === 400 && response.error && typeof response.error === 'object') {
          this.errors = Object.entries(response.error).map(([field, messages]) => ({ field, message: `${this.fieldLabels[field] || field}: ${Array.isArray(messages) ? messages.join(' ') : String(messages)}` }));
          if (this.errors.length) this.showField(this.errors[0].field);
        } else {
          this.notification.show({ type: 'error', text: 'Não foi possível salvar. Seus dados e fotos selecionadas foram mantidos. Tente novamente.' });
        }
      },
    });
  }

  stageImages(files: File[]): void {
    this.pendingImages = files;
  }

  uploadImages(files: File[]): void {
    if (!this.propertyId) {
      return;
    }
    if (this.saving) return;
    this.saving = true;
    this.propertiesService.uploadPropertyImages(this.propertyId, files).subscribe({
      next: () => {
        this.saving = false;
        this.pendingImages = [];
        this.notification.show({ type: 'success', text: 'Fotos enviadas.' });
        this.reloadProperty();
      },
      error: () => { this.saving = false; this.notification.show({ type: 'error', text: 'Falha no envio. As fotos selecionadas foram mantidas. Confira o formato e o limite de 10 MB.' }); },
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


