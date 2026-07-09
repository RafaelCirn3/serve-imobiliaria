import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  template: `
    @if (open) {
      <div class="backdrop">
        <div class="dialog card">
          <h2>{{ title }}</h2>
          <p>{{ message }}</p>
          <div class="actions">
            <button class="btn btn-secondary" type="button" (click)="cancel.emit()">Cancelar</button>
            <button class="btn btn-danger" type="button" (click)="confirm.emit()">Confirmar</button>
          </div>
        </div>
      </div>
    }
  `,
  styles: [`
    .backdrop {
      position: fixed;
      inset: 0;
      z-index: 80;
      display: grid;
      place-items: center;
      background: rgba(0, 0, 0, 0.62);
      padding: 18px;
    }

    .dialog {
      width: min(420px, 100%);
      padding: 24px;
    }

    h2 {
      margin-top: 0;
    }

    p {
      color: #b8b8b8;
    }

    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }
  `],
})
export class ConfirmDialogComponent {
  @Input() open = false;
  @Input() title = 'Confirmar ação';
  @Input() message = 'Deseja continuar?';
  @Output() confirm = new EventEmitter<void>();
  @Output() cancel = new EventEmitter<void>();
}


