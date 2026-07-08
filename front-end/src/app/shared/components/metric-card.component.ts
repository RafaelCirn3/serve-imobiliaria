import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-metric-card',
  standalone: true,
  template: `
    <article class="metric card">
      <span>{{ label }}</span>
      <strong>{{ value }}</strong>
    </article>
  `,
  styles: [`
    .metric {
      padding: 18px;
    }

    span {
      color: #b8b8b8;
      font-size: 0.84rem;
      font-weight: 800;
    }

    strong {
      display: block;
      margin-top: 10px;
      color: #d6b765;
      font-size: 2rem;
    }
  `],
})
export class MetricCardComponent {
  @Input() label = '';
  @Input() value: string | number = 0;
}
