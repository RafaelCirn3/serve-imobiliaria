import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface ToastMessage {
  type: 'success' | 'error' | 'info';
  text: string;
}

@Injectable({ providedIn: 'root' })
export class NotificationService {
  private readonly messageSubject = new BehaviorSubject<ToastMessage | null>(null);
  readonly message$ = this.messageSubject.asObservable();

  show(message: ToastMessage): void {
    this.messageSubject.next(message);
    window.setTimeout(() => this.messageSubject.next(null), 3800);
  }
}


