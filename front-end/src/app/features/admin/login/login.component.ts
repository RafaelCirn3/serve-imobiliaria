import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '@core/services/auth.service';
import { BrandComponent } from '@shared/components/brand.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, BrandComponent],
  template: `
    <main class="login-page">
      <form class="card" [formGroup]="form" (ngSubmit)="login()">
        <app-brand />
        <h1>Acesso administrativo</h1>
        <p>Entre para gerenciar imóveis, leads, banners e regiões da SERVE.</p>
        @if (error) {
          <span class="error">{{ error }}</span>
        }
        <input formControlName="email" placeholder="Email ou usuario">
        <input formControlName="password" type="password" placeholder="Senha">
        <button class="btn btn-primary" type="submit" [disabled]="form.invalid || loading">
          {{ loading ? 'Entrando...' : 'Entrar' }}
        </button>
      </form>
    </main>
  `,
  styles: [`
    .login-page {
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 20px;
      background:
        linear-gradient(90deg, rgba(17, 20, 23, 0.96), rgba(17, 20, 23, 0.55)),
        url('https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1800&q=85') center/cover;
    }

    form {
      width: min(430px, 100%);
      display: grid;
      gap: 14px;
      padding: 28px;
      background: rgba(31, 36, 41, 0.92);
    }

    h1 {
      margin: 12px 0 0;
    }

    p {
      color: #b8b8b8;
      line-height: 1.6;
    }

    input {
      border: 1px solid #30363d;
      border-radius: 8px;
      background: #12161a;
      color: #f5f5f5;
      padding: 13px;
    }

    .error {
      color: #ffb6b3;
      font-weight: 800;
    }
  `],
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  loading = false;
  error = '';
  readonly form = this.fb.nonNullable.group({
    email: ['', Validators.required],
    password: ['', Validators.required],
  });

  login(): void {
    if (this.form.invalid) {
      return;
    }
    this.loading = true;
    const { email, password } = this.form.getRawValue();
    this.auth.login(email, password).subscribe({
      next: () => this.router.navigate(['/admin/dashboard']),
      error: () => {
        this.error = 'Credenciais inválidas.';
        this.loading = false;
      },
    });
  }
}
