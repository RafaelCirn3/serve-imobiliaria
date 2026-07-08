import { Component, Input } from '@angular/core';
import { LeadStatus } from '@core/models/api.models';

@Component({
  selector: 'app-lead-status-badge',
  standalone: true,
  template: `<span [class]="status">{{ label }}</span>`,
  styles: [`
    span {
      display: inline-flex;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 0.78rem;
      font-weight: 900;
      background: rgba(201, 162, 74, 0.13);
      color: #d6b765;
    }

    .finalizado {
      background: rgba(47, 158, 68, 0.14);
      color: #70d989;
    }

    .descartado {
      background: rgba(217, 83, 79, 0.14);
      color: #ffb6b3;
    }
  `],
})
export class LeadStatusBadgeComponent {
  @Input() status: LeadStatus | undefined = 'novo';

  get label(): string {
    const labels: Record<string, string> = {
      novo: 'Novo',
      em_atendimento: 'Em atendimento',
      finalizado: 'Finalizado',
      descartado: 'Descartado',
    };
    return labels[this.status || 'novo'];
  }
}
