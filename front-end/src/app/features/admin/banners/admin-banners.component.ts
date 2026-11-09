import { ControlHintComponent } from '@shared/components/control-hint.component';
import { PhotoComponent } from '@shared/components/photo.component';
import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Banner, BannerPayload } from '@core/models/api.models';
import { BannerService } from '@core/services/banner.service';
import { NotificationService } from '@core/services/notification.service';

@Component({
  selector: 'app-admin-banners',
  standalone: true,
  imports: [ControlHintComponent, PhotoComponent, ReactiveFormsModule],
  template: `
    <div class="admin-page">
      <div class="admin-header"><h1>Carrossel principal</h1></div>
      <form class="card form-grid" [formGroup]="form" (ngSubmit)="save()">
        <label class="field">Titulo<input formControlName="titulo"><app-control-hint [control]="form.controls.titulo" [required]="true" /></label>
        <label class="field">Subtitulo<input formControlName="subtitulo"></label>
        <label class="field">Botao texto<input formControlName="botao_texto"></label>
        <label class="field">Botao link<input formControlName="botao_link"></label>
        <label class="field">Ordem<input type="number" formControlName="ordem"></label>
        <label class="check"><input type="checkbox" formControlName="ativo"> Ativo</label>
        <label class="field full">Imagem<input type="file" accept="image/*" (change)="selectImage($event)"></label>
        @if (preview || editing?.imagem) { <div class="full"><app-photo [src]="preview || editing?.imagem" alt="Prévia da imagem" style="width:100%;max-width:420px;height:220px;border-radius:8px" [eager]="true" /></div> }
        @if (saveError) { <p class="full admin-notice error" role="alert">{{ saveError }}</p> }
        <div class="actions"><button class="btn btn-primary" type="submit" [disabled]="saving">{{ saving ? 'Salvando…' : editing ? 'Atualizar' : 'Cadastrar' }}</button><button class="btn btn-secondary" type="button" (click)="cancelEdit()">Cancelar edição</button></div>
      </form>
      <p class="muted">Escolha as imagens do topo da página inicial. A menor ordem aparece primeiro.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Titulo</th><th>Ativo</th><th>Ordem</th><th>Acoes</th></tr></thead>
          <tbody>
            @for (banner of banners; track banner.id) {
              <tr><td><app-photo [src]="banner.imagem" [alt]="banner.titulo" style="width:120px;height:76px"  />{{ banner.titulo }}</td><td>{{ banner.ativo ? 'Sim' : 'Não' }}</td><td>{{ banner.ordem }}</td><td class="actions"><button class="btn btn-secondary" (click)="edit(banner)">Editar</button><button class="btn btn-danger" (click)="remove(banner)">Excluir</button></td></tr>
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
export class AdminBannersComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly bannersService = inject(BannerService);
  private readonly notification = inject(NotificationService);

  banners: Banner[] = [];
  editing: Banner | null = null;
  imageFile: File | null = null;
  preview = ''; saving = false; saveError = '';
  ngOnDestroy(): void { if(this.preview) URL.revokeObjectURL(this.preview); }
  cancelEdit(): void { this.editing = null; this.imageFile = null; this.ngOnDestroy(); this.preview = ''; this.saveError = ''; this.form.reset(); }

  readonly form = this.fb.nonNullable.group({
    titulo: ['', Validators.required],
    subtitulo: [''],
    botao_texto: [''],
    botao_link: [''],
    ativo: [true],
    ordem: [0],
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.bannersService.listBanners(true).subscribe((response) => (this.banners = response.results));
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
    if(!this.editing && !this.imageFile) { this.saveError = 'Selecione a imagem do carrossel.'; return; }
    const payload: BannerPayload = { ...this.form.getRawValue() };
    if (this.imageFile) {
      payload.imagem = this.imageFile;
    }
    const request = this.editing ? this.bannersService.updateBanner(this.editing.id, payload) : this.bannersService.createBanner(payload);
    this.saving = true;
    request.subscribe({
      next: () => {
        this.saving=false; this.ngOnDestroy(); this.preview='';
        this.notification.show({ type: 'success', text: 'Imagem principal salva.' });
        this.form.reset({ ativo: true, ordem: 0, titulo: '', subtitulo: '', botao_texto: '', botao_link: '' });
        this.editing = null;
        this.imageFile = null;
        this.load();
      },
      error:()=>{ this.saving=false; this.saveError='Não foi possível salvar. Confira os campos e o formato da imagem. Seus dados foram mantidos.'; },
    });
  }

  edit(banner: Banner): void {
    this.ngOnDestroy(); this.preview=''; this.imageFile=null; this.saveError='';
    this.editing = banner;
    this.form.patchValue({
      titulo: banner.titulo,
      subtitulo: banner.subtitulo,
      botao_texto: banner.botao_texto,
      botao_link: banner.botao_link,
      ativo: banner.ativo,
      ordem: banner.ordem,
    });
  }

  remove(banner: Banner): void {
    this.bannersService.deleteBanner(banner.id).subscribe(() => this.load());
  }
}


