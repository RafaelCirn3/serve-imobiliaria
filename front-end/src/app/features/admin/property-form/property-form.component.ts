import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { PropertyImage, PropertyPayload, Region } from '@core/models/api.models';
import { NotificationService } from '@core/services/notification.service';
import { PropertyService } from '@core/services/property.service';
import { RegionService } from '@core/services/region.service';
import { ImageUploaderComponent } from '@shared/components/image-uploader.component';

@Component({
  selector: 'app-property-form',
  standalone: true,
  imports: [ReactiveFormsModule, ImageUploaderComponent],
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
            <label class="field">Tipo<select formControlName="tipo"><option value="apartamento">Apartamento</option><option value="casa">Casa</option><option value="cobertura">Cobertura</option><option value="terreno">Terreno</option><option value="comercial">Comercial</option><option value="condominio">Condomínio</option></select></label>
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
            <label class="field">Cidade<input formControlName="cidade"></label>
            <label class="field">Bairro<input formControlName="bairro"></label>
            <label class="field full">Endereco<input formControlName="endereco"></label>
            <label class="field">CEP<input formControlName="cep"></label>
            <label class="field">Latitude<input formControlName="latitude"></label>
            <label class="field">Longitude<input formControlName="longitude"></label>
          </div>
        }

        @if (tab === 'features') {
          <div class="form-grid">
            <label class="field">Área total<input type="number" formControlName="area_total"></label>
            <label class="field">Área privativa<input type="number" formControlName="area_privativa"></label>
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
      border-color: rgba(201, 162, 74, 0.55);
      color: #c9a24a;
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
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly propertiesService = inject(PropertyService);
  private readonly regionsService = inject(RegionService);
  private readonly notification = inject(NotificationService);

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
    cep: [''],
    latitude: [''],
    longitude: [''],
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

    const payload = this.form.getRawValue() as PropertyPayload;
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
      error: () => this.notification.show({ type: 'error', text: 'Não foi possível salvar o imóvel.' }),
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
