import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AdminSidebarComponent } from '@shared/components/admin-sidebar.component';
import { AdminTopbarComponent } from '@shared/components/admin-topbar.component';

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [RouterOutlet, AdminSidebarComponent, AdminTopbarComponent],
  template: `
    <div class="admin-layout">
      <app-admin-sidebar />
      <main>
        <app-admin-topbar />
        <section class="content">
          <router-outlet />
        </section>
      </main>
    </div>
  `,
  styles: [`
    .admin-layout {
      display: grid;
      grid-template-columns: 260px 1fr;
      min-height: 100vh;
      background: #111417;
    }

    main {
      min-width: 0;
    }

    .content {
      padding: 24px;
    }

    @media (max-width: 820px) {
      .admin-layout {
        grid-template-columns: 1fr;
      }

      app-admin-sidebar {
        display: none;
      }
    }
  `],
})
export class AdminLayoutComponent {}


