import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { Lead, Property } from '@core/models/api.models';
import { LeadService } from '@core/services/lead.service';
import { PropertyService } from '@core/services/property.service';
import { MetricCardComponent } from '@shared/components/metric-card.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [DatePipe, MetricCardComponent],
  template: `
    <div class="admin-page">
      <div class="admin-header"><h1>Dashboard</h1></div>
      <div class="metrics">
        <app-metric-card label="Total de imóveis" [value]="properties.length" />
        <app-metric-card label="Publicados" [value]="publishedCount" />
        <app-metric-card label="Rascunhos" [value]="draftCount" />
        <app-metric-card label="Leads recebidos" [value]="leads.length" />
      </div>
      <div class="columns">
        <section class="card panel">
          <h2>Últimos leads</h2>
          @for (lead of leads.slice(0, 6); track lead.id) {
            <article>
              <strong>{{ lead.nome }}</strong>
              <span>{{ lead.telefone }} · {{ lead.criado_em | date:'dd/MM/yyyy HH:mm' }}</span>
            </article>
          }
        </section>
        <section class="card panel">
          <h2>Últimos imóveis</h2>
          @for (property of properties.slice(0, 6); track property.id) {
            <article>
              <strong>{{ property.titulo }}</strong>
              <span>{{ property.status }} · {{ property.bairro }}</span>
            </article>
          }
        </section>
      </div>
    </div>
  `,
  styles: [`
    .metrics {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
    }

    .columns {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .panel {
      padding: 20px;
    }

    article {
      display: grid;
      gap: 4px;
      border-top: 1px solid #30363d;
      padding: 14px 0;
    }

    span {
      color: #b8b8b8;
    }

    @media (max-width: 980px) {
      .metrics,
      .columns {
        grid-template-columns: 1fr;
      }
    }
  `],
})
export class DashboardComponent implements OnInit {
  private readonly propertiesService = inject(PropertyService);
  private readonly leadsService = inject(LeadService);

  properties: Property[] = [];
  leads: Lead[] = [];

  get publishedCount(): number {
    return this.properties.filter((property) => property.status === 'publicado').length;
  }

  get draftCount(): number {
    return this.properties.filter((property) => property.status === 'rascunho').length;
  }

  ngOnInit(): void {
    this.propertiesService.listAdminProperties().subscribe((response) => (this.properties = response.results));
    this.leadsService.listAdminLeads().subscribe((response) => (this.leads = response.results));
  }
}
