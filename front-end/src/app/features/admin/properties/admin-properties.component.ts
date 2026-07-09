import { CurrencyPipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Property } from '@core/models/api.models';
import { NotificationService } from '@core/services/notification.service';
import { PropertyService } from '@core/services/property.service';
import { ConfirmDialogComponent } from '@shared/components/confirm-dialog.component';

@Component({
  selector: 'app-admin-properties',
  standalone: true,
  imports: [CurrencyPipe, FormsModule, RouterLink, ConfirmDialogComponent],
  template: `
    <div class="admin-page">
      <div class="admin-header">
        <div><h1>Imóveis</h1><p class="muted">Cadastre, edite e inative imóveis.</p></div>
        <a class="btn btn-primary" routerLink="/admin/imoveis/novo">Novo imóvel</a>
      </div>
      <div class="card filters">
        <input [(ngModel)]="search" placeholder="Buscar">
        <select [(ngModel)]="status"><option value="">Status</option><option value="publicado">Publicado</option><option value="rascunho">Rascunho</option><option value="inativo">Inativo</option></select>
        <select [(ngModel)]="tipo"><option value="">Tipo</option><option value="apartamento">Apartamento</option><option value="casa">Casa</option><option value="condominio">Condomínio</option></select>
        <button class="btn btn-secondary" type="button" (click)="load()">Filtrar</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Titulo</th><th>Status</th><th>Tipo</th><th>Valor</th><th>Acoes</th></tr></thead>
          <tbody>
            @for (property of properties; track property.id) {
              <tr>
                <td>{{ property.titulo }}<br><span class="muted">{{ property.bairro }} · {{ property.cidade }}</span></td>
                <td><span class="status-pill">{{ property.status }}</span></td>
                <td>{{ property.tipo }} / {{ property.finalidade }}</td>
                <td>{{ numberValue(property.valor) | currency:'BRL':'symbol':'1.0-0':'pt-BR' }}</td>
                <td class="actions">
                  <a class="btn btn-secondary" [routerLink]="['/imoveis', property.slug]" target="_blank">Ver</a>
                  <a class="btn btn-secondary" [routerLink]="['/admin/imoveis', property.id, 'editar']">Editar</a>
                  <button class="btn btn-danger" type="button" (click)="askDelete(property)">Inativar</button>
                </td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    </div>
    <app-confirm-dialog [open]="!!selected" title="Inativar imóvel" message="O imóvel deixará de aparecer no site público." (cancel)="selected = null" (confirm)="deleteSelected()" />
  `,
  styles: [`
    .filters {
      display: grid;
      grid-template-columns: 1fr 180px 180px auto;
      gap: 10px;
      padding: 14px;
    }

    input,
    select {
      border: 1px solid #30363d;
      border-radius: 8px;
      background: #12161a;
      color: #f5f5f5;
      padding: 10px;
    }

    @media (max-width: 840px) {
      .filters {
        grid-template-columns: 1fr;
      }
    }
  `],
})
export class AdminPropertiesComponent implements OnInit {
  private readonly propertiesService = inject(PropertyService);
  private readonly notification = inject(NotificationService);

  properties: Property[] = [];
  selected: Property | null = null;
  search = '';
  status = '';
  tipo = '';

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.propertiesService.listAdminProperties({ search: this.search, status: this.status, tipo: this.tipo }).subscribe((response) => {
      this.properties = response.results;
    });
  }

  numberValue(value: string | number): number {
    return Number(value || 0);
  }

  askDelete(property: Property): void {
    this.selected = property;
  }

  deleteSelected(): void {
    if (!this.selected) {
      return;
    }
    this.propertiesService.deleteProperty(this.selected.id).subscribe(() => {
      this.notification.show({ type: 'success', text: 'Imóvel inativado.' });
      this.selected = null;
      this.load();
    });
  }
}


