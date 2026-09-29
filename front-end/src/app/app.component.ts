import { Component, computed, inject } from '@angular/core';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { filter, map, startWith } from 'rxjs';
import { ToastComponent } from './shared/components/toast.component';
import { SaleDialogComponent } from './shared/components/sale-dialog.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, ToastComponent, SaleDialogComponent],
  template: `
    <router-outlet />
    <app-toast />
    @if (publicPage()) { <app-sale-dialog /> }
  `,
})
export class AppComponent {
  private readonly router = inject(Router);
  private readonly url = toSignal(this.router.events.pipe(filter((event) => event instanceof NavigationEnd), map((event) => event.urlAfterRedirects), startWith(this.router.url)), { initialValue: this.router.url });
  readonly publicPage = computed(() => !this.url().split('?')[0].startsWith('/admin'));
}


