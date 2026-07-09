import { AsyncPipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { NotificationService } from '@core/services/notification.service';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [AsyncPipe],
  template: `
    @if (notification.message$ | async; as message) {
      <div class="toast" [class]="message.type">{{ message.text }}</div>
    }
  `,
  styles: [`
    .toast {
      position: fixed;
      right: 18px;
      bottom: 18px;
      z-index: 100;
      max-width: min(380px, calc(100vw - 36px));
      border: 1px solid #30363d;
      border-radius: 8px;
      background: #1f2429;
      color: #f5f5f5;
      padding: 14px 16px;
      box-shadow: 0 18px 50px rgba(0, 0, 0, 0.32);
    }

    .success {
      border-color: rgba(47, 158, 68, 0.55);
    }

    .error {
      border-color: rgba(217, 83, 79, 0.65);
    }
  `],
})
export class ToastComponent {
  readonly notification = inject(NotificationService);
}


