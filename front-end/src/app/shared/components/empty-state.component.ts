import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  template: `
    <div class="empty card">
      <strong>{{ title }}</strong>
      <p>{{ message }}</p>
    </div>
  `,
  styles: [`
    .empty {
      padding: 34px;
      text-align: center;
    }

    strong {
      color: #fff;
      font-size: 1.2rem;
    }

    p {
      color: #b8b8b8;
      margin-bottom: 0;
    }
  `],
})
export class EmptyStateComponent {
  @Input() title = 'Nenhum resultado encontrado';
  @Input() message = 'Ajuste os filtros ou tente uma nova busca.';
}


