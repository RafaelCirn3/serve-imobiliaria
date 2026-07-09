import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Banner, BannerPayload } from '@core/models/api.models';
import { BannerService } from '@core/services/banner.service';
import { NotificationService } from '@core/services/notification.service';

@Component({
  selector: 'app-admin-banners',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="admin-page">
      <div class="admin-header"><h1>Banners</h1></div>
      <form class="card form-grid" [formGroup]="form" (ngSubmit)="save()">
        <label class="field">Titulo<input formControlName="titulo"></label>
        <label class="field">Subtitulo<input formControlName="subtitulo"></label>
        <label class="field">Botao texto<input formControlName="botao_texto"></label>
        <label class="field">Botao link<input formControlName="botao_link"></label>
        <label class="field">Ordem<input type="number" formControlName="ordem"></label>
        <label class="check"><input type="checkbox" formControlName="ativo"> Ativo</label>
        <label class="field full">Imagem<input type="file" accept="image/*" (change)="selectImage($event)"></label>
        <button class="btn btn-primary" type="submit">{{ editing ? 'Atualizar' : 'Cadastrar' }}</button>
      </form>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Titulo</th><th>Ativo</th><th>Ordem</th><th>Acoes</th></tr></thead>
          <tbody>
            @for (banner of banners; track banner.id) {
              <tr><td>{{ banner.titulo }}</td><td>{{ banner.ativo ? 'Sim' : 'Não' }}</td><td>{{ banner.ordem }}</td><td class="actions"><button class="btn btn-secondary" (click)="edit(banner)">Editar</button><button class="btn btn-danger" (click)="remove(banner)">Excluir</button></td></tr>
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
export class AdminBannersComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly bannersService = inject(BannerService);
  private readonly notification = inject(NotificationService);

  banners: Banner[] = [];
  editing: Banner | null = null;
  imageFile: File | null = null;
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
    this.imageFile = ((event.target as HTMLInputElement).files || [])[0] || null;
  }

  save(): void {
    const payload: BannerPayload = { ...this.form.getRawValue() };
    if (this.imageFile) {
      payload.imagem = this.imageFile;
    }
    const request = this.editing ? this.bannersService.updateBanner(this.editing.id, payload) : this.bannersService.createBanner(payload);
    request.subscribe({
      next: () => {
        this.notification.show({ type: 'success', text: 'Banner salvo.' });
        this.form.reset({ ativo: true, ordem: 0, titulo: '', subtitulo: '', botao_texto: '', botao_link: '' });
        this.editing = null;
        this.imageFile = null;
        this.load();
      },
    });
  }

  edit(banner: Banner): void {
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


