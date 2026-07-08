import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Region } from '@core/models/api.models';
import { NotificationService } from '@core/services/notification.service';
import { RegionService } from '@core/services/region.service';

@Component({
  selector: 'app-admin-regions',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="admin-page">
      <div class="admin-header"><h1>Regiões</h1></div>
      <form class="card form-grid" [formGroup]="form" (ngSubmit)="save()">
        <label class="field">Nome<input formControlName="nome"></label>
        <label class="field">Cidade<input formControlName="cidade"></label>
        <label class="field full">Descrição<textarea formControlName="descricao"></textarea></label>
        <label class="check"><input type="checkbox" formControlName="ativo"> Ativa</label>
        <label class="field full">Imagem<input type="file" accept="image/*" (change)="selectImage($event)"></label>
        <button class="btn btn-primary" type="submit">{{ editing ? 'Atualizar' : 'Cadastrar' }}</button>
      </form>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Nome</th><th>Cidade</th><th>Ativa</th><th>Acoes</th></tr></thead>
          <tbody>
            @for (region of regions; track region.id) {
              <tr><td>{{ region.nome }}</td><td>{{ region.cidade }}</td><td>{{ region.ativo ? 'Sim' : 'Não' }}</td><td class="actions"><button class="btn btn-secondary" (click)="edit(region)">Editar</button><button class="btn btn-danger" (click)="remove(region)">Excluir</button></td></tr>
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
export class AdminRegionsComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly regionsService = inject(RegionService);
  private readonly notification = inject(NotificationService);

  regions: Region[] = [];
  editing: Region | null = null;
  imageFile: File | null = null;
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
    this.imageFile = ((event.target as HTMLInputElement).files || [])[0] || null;
  }

  save(): void {
    const payload: Partial<Region> = { ...this.form.getRawValue() };
    if (this.imageFile) {
      payload.imagem = this.imageFile;
    }
    const request = this.editing ? this.regionsService.updateRegion(this.editing.id, payload) : this.regionsService.createRegion(payload);
    request.subscribe({
      next: () => {
        this.notification.show({ type: 'success', text: 'Regiao salva.' });
        this.form.reset({ nome: '', cidade: 'João Pessoa', descricao: '', ativo: true });
        this.editing = null;
        this.imageFile = null;
        this.load();
      },
    });
  }

  edit(region: Region): void {
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
