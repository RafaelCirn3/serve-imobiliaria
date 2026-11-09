import { ControlHintComponent } from '@shared/components/control-hint.component';
import { PhotoComponent } from '@shared/components/photo.component';
import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Region, RegionPayload } from '@core/models/api.models';
import { NotificationService } from '@core/services/notification.service';
import { RegionService } from '@core/services/region.service';

@Component({
  selector: 'app-admin-regions',
  standalone: true,
  imports: [ControlHintComponent, PhotoComponent, ReactiveFormsModule],
  template: `
    <div class="admin-page">
      <div class="admin-header"><h1>Regiões</h1></div>
      <form class="card form-grid" [formGroup]="form" (ngSubmit)="save()">
        <label class="field">Nome<input formControlName="nome"><app-control-hint [control]="form.controls.nome" [required]="true" /></label>
        <label class="field">Cidade<input formControlName="cidade"><app-control-hint [control]="form.controls.cidade" [required]="true" /></label>
        <label class="field full">Descrição<textarea formControlName="descricao"></textarea></label>
        <label class="check"><input type="checkbox" formControlName="ativo"> Ativa</label>
        <label class="field full">Imagem<input type="file" accept="image/*" (change)="selectImage($event)"></label>
        @if (preview || editing?.imagem) { <div class="full"><app-photo [src]="preview || editing?.imagem" alt="Prévia da imagem" style="width:100%;max-width:420px;height:220px;border-radius:8px" [eager]="true" /></div> }
        @if (saveError) { <p class="full admin-notice error" role="alert">{{ saveError }}</p> }
        <div class="actions"><button class="btn btn-primary" type="submit" [disabled]="saving">{{ saving ? 'Salvando…' : editing ? 'Atualizar' : 'Cadastrar' }}</button><button class="btn btn-secondary" type="button" (click)="cancelEdit()">Cancelar edição</button></div>
      </form>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Nome</th><th>Cidade</th><th>Ativa</th><th>Acoes</th></tr></thead>
          <tbody>
            @for (region of regions; track region.id) {
              <tr><td><app-photo [src]="region.imagem" [alt]="region.nome" style="width:120px;height:76px;border-radius:6px;margin-bottom:10px" />{{ region.nome }}</td><td>{{ region.cidade }}</td><td>{{ region.ativo ? 'Sim' : 'Não' }}</td><td class="actions"><button class="btn btn-secondary" (click)="edit(region)">Editar</button><button class="btn btn-danger" (click)="remove(region)">Excluir</button></td></tr>
            }
          </tbody>
        </table>
      </div>
    </div>
  `,
  styles: [`
    form {
      padding: 18px;
    }

    .full {
      grid-column: 1 / -1;
    }

    .check {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  `],
})
export class AdminRegionsComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly regionsService = inject(RegionService);
  private readonly notification = inject(NotificationService);

  regions: Region[] = [];
  editing: Region | null = null;
  imageFile: File | null = null;
  preview = ''; saving = false; saveError = '';
  ngOnDestroy(): void { if(this.preview) URL.revokeObjectURL(this.preview); }
  cancelEdit(): void { this.editing = null; this.imageFile = null; this.ngOnDestroy(); this.preview = ''; this.saveError = ''; this.form.reset(); }

  readonly form = this.fb.nonNullable.group({
    nome: ['', Validators.required],
    cidade: ['João Pessoa', Validators.required],
    descricao: [''],
    ativo: [true],
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.regionsService.listRegions(true).subscribe((response) => (this.regions = response.results));
  }

  selectImage(event: Event): void {
    const file = ((event.target as HTMLInputElement).files || [])[0];
    if(!file) return;
    this.ngOnDestroy(); this.imageFile = file; this.preview = URL.createObjectURL(file);
  }

  save(): void {
    if(this.saving) return;
    this.form.markAllAsTouched(); this.saveError = '';
    if(this.form.invalid) { this.saveError = 'Preencha os campos obrigatórios indicados.'; return; }
    const payload: RegionPayload = { ...this.form.getRawValue() };
    if (this.imageFile) {
      payload.imagem = this.imageFile;
    }
    const request = this.editing ? this.regionsService.updateRegion(this.editing.id, payload) : this.regionsService.createRegion(payload);
    this.saving = true;
    request.subscribe({
      next: () => {
        this.saving=false; this.ngOnDestroy(); this.preview='';
        this.notification.show({ type: 'success', text: 'Regiao salva.' });
        this.form.reset({ nome: '', cidade: 'João Pessoa', descricao: '', ativo: true });
        this.editing = null;
        this.imageFile = null;
        this.load();
      },
      error:()=>{ this.saving=false; this.saveError='Não foi possível salvar. Confira os campos e o formato da imagem. Seus dados foram mantidos.'; },
    });
  }

  edit(region: Region): void {
    this.ngOnDestroy(); this.preview=''; this.imageFile=null; this.saveError='';
    this.editing = region;
    this.form.patchValue({
      nome: region.nome,
      cidade: region.cidade,
      descricao: region.descricao,
      ativo: region.ativo,
    });
  }

  remove(region: Region): void {
    this.regionsService.deleteRegion(region.id).subscribe(() => this.load());
  }
}


