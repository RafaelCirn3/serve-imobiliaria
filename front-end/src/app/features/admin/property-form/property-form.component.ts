import { PhotoComponent } from '@shared/components/photo.component';
import { ControlHintComponent } from '@shared/components/control-hint.component';
import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
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
  imports: [PhotoComponent, ControlHintComponent, RouterLink, ReactiveFormsModule, ImageUploaderComponent, AddressEditorComponent, PropertyMapComponent],
  template: `
    <div class="admin-page">
      <div class="admin-header">
        <div>
          <a class="back-link" routerLink="/admin/imoveis">← Todos os imóveis</a><h1>{{ propertyId ? 'Editar imóvel' : 'Novo imóvel' }}</h1>
          <p class="muted">Comece pelas informações principais. Você pode salvar e continuar depois.</p>
        </div>
        <button class="btn btn-primary" type="button" [disabled]="saving || loading || !!loadError" (click)="save()">{{ saving ? "Salvando…" : "Salvar" }}</button>
      </div>

      <div class="form-progress"><div><strong>{{ completedRequired }} de {{ requiredFields.length }} campos obrigatórios preenchidos</strong><span>{{ propertyId ? (form.dirty || pendingImages.length ? 'Alterações não salvas' : 'Cadastro salvo') : 'Novo cadastro' }}</span></div><progress [value]="completedRequired" [max]="requiredFields.length" aria-label="Preenchimento dos campos obrigatórios"></progress></div>
      @if (loadError) { <p class="admin-notice error" role="alert">{{ loadError }}</p> }
      <nav class="tabs" aria-label="Etapas do cadastro">
        @for (item of tabs; track item.id; let index = $index) {
          <button type="button" [class.active]="tab === item.id" [attr.aria-current]="tab === item.id ? 'step' : null" [class.has-error]="tabHasErrors(item.id)" (click)="tab = item.id"><span class="step-number">{{ tabHasErrors(item.id) ? '!' : sectionComplete(item.id) ? '✓' : index + 1 }}</span><span>{{ item.label }}<small>{{ stepHint(item.id) }}</small></span></button>
        }
      </nav>

      @if (draftRestored) { <p role="status">Rascunho recuperado neste navegador. Fotos precisam ser selecionadas novamente após recarregar a página. <button class="btn btn-secondary" type="button" (click)="discardDraft()">Descartar rascunho recuperado</button></p> }
      @if (errors.length) { <div class="error-summary" role="alert"><strong>Confira antes de salvar:</strong><ul>@for (error of errors; track $index) { <li><button type="button" (click)="showField(error.field)">{{ error.message }}</button></li> }</ul></div> }
      <div class="property-workspace">
      <form class="card form-card" [formGroup]="form" (ngSubmit)="save()">
        <fieldset [disabled]="saving || loading || !!loadError">
        <div [hidden]="tab !== 'basic'">
          <div class="form-grid">
            <label class="field">Título *<input formControlName="titulo"><app-control-hint [control]="form.controls.titulo" [required]="true" /></label>
            <label class="field">Valor *<input type="number" min="0" step="0.01" inputmode="decimal" formControlName="valor"><app-control-hint [control]="form.controls.valor" [required]="true" /></label>
            <label class="field full">Descrição *<textarea formControlName="descricao"></textarea><app-control-hint [control]="form.controls.descricao" [required]="true" /></label>
            <label class="field">Tipo<select formControlName="tipo">
              @for (type of propertyTypes; track type.value) { <option [value]="type.value">{{ type.label }}</option> }
            </select><app-control-hint [control]="form.controls.tipo" [required]="false" /></label>
            <label class="field">Finalidade<select formControlName="finalidade"><option value="venda">Venda</option><option value="aluguel">Aluguel</option></select><app-control-hint [control]="form.controls.finalidade" [required]="false" /></label>
            <label class="field">Condomínio<input type="number" min="0" step="0.01" inputmode="decimal" formControlName="valor_condominio"><app-control-hint [control]="form.controls.valor_condominio" [required]="false" /></label>
            <label class="field">IPTU<input type="number" min="0" step="0.01" inputmode="decimal" formControlName="valor_iptu"><app-control-hint [control]="form.controls.valor_iptu" [required]="false" /></label>
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
            <app-control-hint [control]="form.controls.regiao" [required]="false" /></label>
            <app-address-editor [form]="form" listId="admin-address" />
            <label class="field full">Endereço anterior / referência<input formControlName="endereco"><app-control-hint [control]="form.controls.endereco" [required]="false" /></label>
            <label class="field">Latitude<input formControlName="latitude"><app-control-hint [control]="form.controls.latitude" [required]="false" /></label>
            <label class="field">Longitude<input formControlName="longitude"><app-control-hint [control]="form.controls.longitude" [required]="false" /></label>
            <button type="button" class="btn btn-secondary" [disabled]="geocoding" (click)="geocode()">{{ geocoding ? 'Localizando…' : 'Localizar endereço no mapa' }}</button>
            <label class="check"><input type="checkbox" formControlName="localizacao_exata"> Publicar localização exata (posição conferida)</label>
            <p class="muted full">A posição é aproximada por padrão. Ao publicar a localização exata, número e complemento também ficam disponíveis ao público.</p>
            @if (mapPreview.length) { <div class="full"><app-property-map [properties]="mapPreview" [editable]="true" (positionChanged)="movePosition($event)" /></div> }
          </div>
        </div>

        <div [hidden]="tab !== 'features'">
          <div class="form-grid">
            <label class="field">Área total (m²)<input type="number" min="0" step="0.01" formControlName="area_total"><app-control-hint [control]="form.controls.area_total" [required]="false" /></label>
            <label class="field">Área privativa (m²)<input type="number" min="0" step="0.01" formControlName="area_privativa"><app-control-hint [control]="form.controls.area_privativa" [required]="false" /></label>
            @if (form.controls.tipo.value === 'terreno') {
              <p class="muted full">Para áreas e terrenos, informe a metragem no campo Área total.</p>
            }
            <label class="field">Quartos<input type="number" min="0" step="1" inputmode="numeric" formControlName="quartos"><app-control-hint [control]="form.controls.quartos" [required]="false" /></label>
            <label class="field">Suítes<input type="number" min="0" step="1" inputmode="numeric" formControlName="suites"><app-control-hint [control]="form.controls.suites" [required]="false" /></label>
            <label class="field">Banheiros<input type="number" min="0" step="1" inputmode="numeric" formControlName="banheiros"><app-control-hint [control]="form.controls.banheiros" [required]="false" /></label>
            <label class="field">Vagas<input type="number" min="0" step="1" inputmode="numeric" formControlName="vagas"><app-control-hint [control]="form.controls.vagas" [required]="false" /></label>
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
            <label class="field">Status<select formControlName="status"><option value="rascunho">Rascunho</option><option value="publicado">Publicado</option><option value="vendido">Vendido</option><option value="alugado">Alugado</option><option value="inativo">Inativo</option></select><app-control-hint [control]="form.controls.status" [required]="false" /></label>
            <label class="check"><input type="checkbox" formControlName="destaque"> Imóvel em destaque</label>
            <label class="field full">Título para buscadores (opcional)<input formControlName="titulo_seo"><app-control-hint [control]="form.controls.titulo_seo" [required]="false" /></label>
            <label class="field full">Descrição para buscadores (opcional)<textarea formControlName="descricao_seo"></textarea><app-control-hint [control]="form.controls.descricao_seo" [required]="false" /></label>
          </div>
        </div>
        <p class="muted">{{ form.controls.status.value === 'publicado' ? 'Ao salvar, este imóvel ficará visível no site.' : 'Este imóvel não será exibido no site enquanto estiver como rascunho, vendido, alugado ou inativo.' }}</p>
        <button class="btn btn-primary" type="submit" [disabled]="saving">{{ saving ? 'Salvando…' : 'Salvar imóvel e fotos' }}</button>
        <div class="step-actions"><button class="btn btn-secondary" type="button" [disabled]="tab === 'basic'" (click)="moveStep(-1)">← Etapa anterior</button><button class="btn btn-secondary" type="button" [disabled]="tab === 'seo'" (click)="moveStep(1)">Próxima etapa →</button></div>
        </fieldset>
      </form>
      <aside class="card property-preview" aria-label="Resumo do imóvel">
        <div class="preview-heading"><strong>Apresentação do imóvel</strong><span class="admin-badge" [attr.data-status]="form.controls.status.value">{{ form.controls.status.value === 'publicado' ? 'Publicado' : 'Rascunho / gestão' }}</span></div>
        <div class="preview-cover"><app-photo [src]="previewCover" [alt]="form.controls.titulo.value || 'Prévia do imóvel'" [eager]="true" /></div>
        <div class="preview-body"><span class="muted">{{ images.length }} foto(s) salva(s){{ pendingImages.length ? ' · ' + pendingImages.length + ' aguardando envio' : '' }}</span><h2>{{ form.controls.titulo.value || 'Seu imóvel aparece aqui' }}</h2><p>{{ form.controls.bairro.value || 'Bairro' }} · {{ form.controls.cidade.value }}</p>
          <button class="btn btn-secondary" type="button" (click)="tab = 'photos'">{{ images.length ? 'Gerenciar fotos' : 'Adicionar fotos' }}</button>
          <div class="preview-checks"><strong>Antes de publicar</strong><span [class.done]="completedRequired === requiredFields.length">{{ completedRequired === requiredFields.length ? '✓' : '○' }} Informações obrigatórias</span><span [class.done]="!!(images.length + pendingImages.length)">{{ images.length + pendingImages.length ? '✓' : '○' }} Fotos do imóvel <small>(recomendado)</small></span><span [class.done]="form.controls.status.value === 'publicado'">{{ form.controls.status.value === 'publicado' ? '✓' : '○' }} Status definido como Publicado</span></div>
          <p class="save-guidance">Salvar guarda o cadastro. Para aparecer no site, escolha Publicado na última etapa.</p>
        </div>
      </aside>
      </div>
    </div>
  `,
  styles: [`
    fieldset { border:0;padding:0;margin:0;min-width:0; } [hidden] {display:none !important;}
    .back-link {display:block;margin-bottom:14px;font-size:12px;color:#687e8b;}
    .form-progress {display:grid;gap:12px;background:#fff;border:1px solid #e2e7eb;border-radius:10px;padding:16px 20px;}
    .form-progress>div {display:flex;justify-content:space-between;gap:12px;font-size:12px;color:#647681;flex-wrap:wrap;}
    progress {width:100%;height:5px;border:0;border-radius:10px;overflow:hidden;accent-color:#385d65;} progress::-webkit-progress-bar{background:#edf1f3;} progress::-webkit-progress-value{background:#385d65;}
    .tabs {display:flex;gap:8px;flex-wrap:wrap;} .tabs button {display:flex;align-items:center;gap:9px;border:1px solid #dfe5e9;border-radius:9px;background:#fff;color:#6a7c88;padding:13px;font-size:12px;text-align:left;flex:1;min-width:130px;}
    .tabs button.active {border-color:#344e5c;background:#edf3f5;color:#263f4b;box-shadow:0 0 0 1px #344e5c;}
    .tabs button.has-error {border-color:#c47364;color:#9d4031;}.tabs small{display:block;font-size:10px;font-weight:400;margin-top:5px;opacity:.85;}.step-number{width:24px;height:24px;display:grid;place-items:center;border-radius:50%;background:#edf1f3;flex:0 0 24px;}.active .step-number{background:#344e5c;color:white;}
    .property-workspace {display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:24px;align-items:start;}
    .form-card {padding:28px;min-width:0;}.full {grid-column:1/-1;}.check{display:flex;align-items:center;gap:8px;}.error-summary button{background:transparent;border:0;color:inherit;text-align:left;text-decoration:underline;padding:8px;}
    .step-actions {display:flex;justify-content:space-between;gap:12px;margin-top:24px;padding-top:20px;border-top:1px solid #e8edf0;}
    .property-preview {position:sticky;top:100px;overflow:hidden;}.preview-heading{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:16px;font-size:11px;}.preview-cover{aspect-ratio:16/11;}.preview-body{display:grid;gap:14px;padding:20px;}.preview-body>span,.preview-body>p{font-size:12px;line-height:1.6;margin:0;}.preview-body h2{font-size:17px;line-height:1.4;margin:0;}.preview-checks{border-top:1px solid #edf0f2;padding-top:18px;display:grid;gap:12px;font-size:12px;color:#8a7861;}.preview-checks strong{color:#536573;}.preview-checks .done{color:#286747;}.save-guidance{color:#7b8790;}
    @media(max-width:1150px){.property-workspace{grid-template-columns:minmax(0,1fr) 245px;gap:16px;}.form-card{padding:20px;}}
    @media(max-width:1000px){.property-workspace{grid-template-columns:1fr;}.property-preview{position:static;display:grid;grid-template-columns:180px 1fr;}.preview-heading{grid-column:1/-1;}.preview-cover{aspect-ratio:auto;min-height:160px;}.preview-checks,.save-guidance{display:none;}.preview-body{padding:16px;}.property-preview{grid-row:1;}.tabs button{min-width:110px;}.tabs small{display:none;}}
    @media(max-width:560px){.tabs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));}.tabs button{min-width:0;padding:12px;font-size:11px;}.tabs button>span:last-child{min-width:0;overflow-wrap:anywhere;}.property-preview{display:block;}.preview-cover{height:160px;min-height:0;}.preview-body{gap:10px;}}
    @media(max-width:480px){.property-preview{grid-template-columns:100px 1fr;}.preview-cover{min-height:150px;}.preview-body h2{font-size:14px;}.form-card{padding:18px;}.step-actions .btn{font-size:11px;padding:0 10px;}}
  `],
})
export class PropertyFormComponent implements OnInit, OnDestroy {
  readonly propertyTypes = PROPERTY_TYPES;
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly propertiesService = inject(PropertyService);
  private readonly regionsService = inject(RegionService);
  private readonly notification = inject(NotificationService);
  private readonly locations = inject(LocationService);
  private readonly destroyRef = inject(DestroyRef);
  readonly requiredFields = ['titulo','descricao','valor','cidade','bairro'] as const;
  loading = false; loadError = ''; private pendingPreview = '';
  get completedRequired(): number { return this.requiredFields.filter(field => this.form.controls[field].valid).length; }
  get previewCover(): string { return this.pendingPreview || this.images.find(image=>image.imagem_capa)?.imagem || this.images[0]?.imagem || ''; }
  sectionComplete(id: string): boolean {
    if (this.tabHasErrors(id)) return false;
    if (id === 'basic') return ['titulo','descricao','valor'].every(field=>this.form.get(field)?.valid);
    if (id === 'location') return ['cidade','bairro'].every(field=>this.form.get(field)?.valid);
    if (id === 'photos') return !!(this.images.length + this.pendingImages.length);
    if (id === 'seo') return this.form.controls.status.value === 'publicado';
    return false;
  }
  stepHint(id:string):string { return this.tabHasErrors(id) ? 'Revisar campos' : id === 'photos' ? `${this.images.length + this.pendingImages.length} foto(s)` : id === 'features' ? 'Complementar' : this.sectionComplete(id) ? 'Preenchido' : id === 'seo' ? 'Escolha a visibilidade' : 'Preencher'; }
  moveStep(direction:number):void { const index=this.tabs.findIndex(item=>item.id===this.tab);this.tab=this.tabs[Math.min(this.tabs.length-1,Math.max(0,index+direction))].id; }
  ngOnDestroy():void { if(this.pendingPreview) URL.revokeObjectURL(this.pendingPreview); }
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
    this.form.markAsPristine();
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
      this.loading = true;
      this.propertiesService.getAdminProperty(this.propertyId).subscribe({next: property => {
        this.form.patchValue(property as never); this.images = property.imagens;
        this.restoreDraft(); this.loading = false;
      },error:()=>{this.loading=false;this.loadError='Não foi possível abrir este imóvel. Volte à lista e tente novamente.';}});
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
    if (this.saving || this.loading || this.loadError) return;
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
              this.stageImages([]);
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
          for(const error of this.errors) this.form.get(error.field)?.setErrors({server:error.message});
          if (this.errors.length) this.showField(this.errors[0].field);
        } else {
          this.notification.show({ type: 'error', text: 'Não foi possível salvar. Seus dados e fotos selecionadas foram mantidos. Tente novamente.' });
        }
      },
    });
  }

  stageImages(files: File[]): void {
    this.pendingImages = files;
    if(this.pendingPreview) URL.revokeObjectURL(this.pendingPreview);
    const file=files.find(item=>!/heic|heif/i.test(item.type + item.name));
    this.pendingPreview=file ? URL.createObjectURL(file) : '';
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
        this.stageImages([]);
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
    if (!this.propertyId || this.saving || !confirm('Excluir esta foto do imóvel?')) return;
    this.saving = true;
    this.propertiesService.deletePropertyImage(this.propertyId, image.id).subscribe({
      next:()=>{this.images=this.images.filter(item=>item.id!==image.id);this.saving=false;this.notification.show({type:'success',text:'Foto excluída.'});},
      error:()=>{this.saving=false;this.notification.show({type:'error',text:'Não foi possível excluir esta foto.'});},
    });
  }

  makeCover(image: PropertyImage): void {
    if (!this.propertyId || this.saving) return;
    this.saving = true;
    this.propertiesService.updatePropertyImage(this.propertyId, image.id, {imagem_capa:true}).subscribe({
      next:()=>{this.images=this.images.map(item=>({...item,imagem_capa:item.id===image.id}));this.saving=false;this.notification.show({type:'success',text:'Foto de capa atualizada.'});},
      error:()=>{this.saving=false;this.notification.show({type:'error',text:'Não foi possível definir a capa. Tente novamente.'});},
    });
  }

  private reloadProperty(): void {
    if (!this.propertyId) {
      return;
    }
    this.propertiesService.getAdminProperty(this.propertyId).subscribe((property) => (this.images = property.imagens));
  }
}


