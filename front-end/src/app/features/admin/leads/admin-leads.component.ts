import { DatePipe } from '@angular/common';
import { KeyValuePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { Lead, LeadStatus } from '@core/models/api.models';
import { LeadService } from '@core/services/lead.service';
import { NotificationService } from '@core/services/notification.service';
import { LeadStatusBadgeComponent } from '@shared/components/lead-status-badge.component';

@Component({
  selector: 'app-admin-leads',
  standalone: true,
  imports: [DatePipe, KeyValuePipe, LeadStatusBadgeComponent],
  template: `
    <div class="admin-page">
      <div class="admin-header"><h1>Leads</h1></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Contato</th><th>Imóvel</th><th>Mensagem</th><th>Status</th><th>Data</th><th>Ação</th></tr></thead>
          <tbody>
            @for (lead of leads; track lead.id) {
              <tr>
                <td><strong>{{ lead.nome }}</strong><br><span class="muted">{{ lead.telefone }} · {{ lead.email }}</span></td>
                <td>{{ lead.origem === 'venda_imovel' ? 'Oferta de venda' : lead.imovel_titulo || 'Contato geral' }}
                  @for (field of lead.dados_imovel | keyvalue; track field.key) {
                    @if (field.value !== null && field.value !== '') { <div class="muted">{{ detailLabels[field.key] || field.key }}: {{ field.value }}</div> }
                  }
                </td>
                <td>{{ lead.mensagem }}</td>
                <td><app-lead-status-badge [status]="lead.status" /></td>
                <td>{{ lead.criado_em | date:'dd/MM/yyyy HH:mm' }}</td>
                <td>
                  <select [value]="lead.status" (change)="updateStatus(lead, $event)">
                    <option value="novo">Novo</option>
                    <option value="em_atendimento">Em atendimento</option>
                    <option value="finalizado">Finalizado</option>
                    <option value="descartado">Descartado</option>
                  </select>
                  @if (lead.origem === 'venda_imovel') {
                    <p>E-mail: {{ lead.notificacao_status === 'enviado' ? 'Enviado' : 'Pendente' }}</p>
                    @if (lead.notificacao_status !== 'enviado') {
                      <button type="button" class="btn btn-secondary" [disabled]="retrying === lead.id" (click)="retry(lead)">Reenviar e-mail</button>
                    }
                  }
                </td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    </div>
  `,
  styles: [`
    select {
      border: 1px solid #30363d;
      border-radius: 8px;
      background: #12161a;
      color: #f5f5f5;
      padding: 9px;
    }
  `],
})
export class AdminLeadsComponent implements OnInit {
  private readonly leadsService = inject(LeadService);
  private readonly notification = inject(NotificationService);
  leads: Lead[] = [];
  readonly detailLabels: Record<string, string> = { tipo: 'Tipo', cep: 'CEP', cidade: 'Cidade', uf: 'UF', bairro: 'Bairro', logradouro: 'Rua', numero: 'Número', complemento: 'Complemento', quartos: 'Quartos', area_total: 'Área total (m²)', valor: 'Valor pretendido (R$)' };
  retrying: number | null = null;

  retry(lead: Lead): void {
    this.retrying = lead.id;
    this.leadsService.retryNotification(lead.id).subscribe({
      next: (updated) => {
        Object.assign(lead, updated); this.retrying = null;
        this.notification.show({ type: updated.notificacao_status === 'enviado' ? 'success' : 'error', text: updated.notificacao_status === 'enviado' ? 'Notificação enviada.' : 'A notificação continua pendente. Verifique a configuração de e-mail.' });
      },
      error: () => { this.retrying = null; this.notification.show({ type: 'error', text: 'Não foi possível reenviar.' }); },
    });
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.leadsService.listAdminLeads().subscribe((response) => (this.leads = response.results));
  }

  updateStatus(lead: Lead, event: Event): void {
    const status = (event.target as HTMLSelectElement).value as LeadStatus;
    this.leadsService.updateLeadStatus(lead.id, status).subscribe({
      next: (updated) => {
        lead.status = updated.status;
        this.notification.show({ type: 'success', text: 'Status do lead atualizado.' });
      },
    });
  }
}


