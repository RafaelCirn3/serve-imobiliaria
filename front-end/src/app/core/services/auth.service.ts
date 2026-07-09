import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { environment } from '@env/environment';
import { LoginResponse } from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly accessKey = 'serve_access_token';
  private readonly refreshKey = 'serve_refresh_token';
  private readonly userKey = 'serve_admin_user';
  private readonly authState = new BehaviorSubject<boolean>(this.isAuthenticated());

  readonly isAuthenticated$ = this.authState.asObservable();

  login(email: string, password: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${environment.apiUrl}/auth/login/`, {
        username: email,
        password,
      })
      .pipe(
        tap((response) => {
          localStorage.setItem(this.accessKey, response.access);
          localStorage.setItem(this.refreshKey, response.refresh);
          localStorage.setItem(this.userKey, JSON.stringify(response.user));
          this.authState.next(true);
        }),
      );
  }

  logout(): void {
    const refresh = this.getRefreshToken();
    if (refresh) {
      this.http.post(`${environment.apiUrl}/auth/logout/`, { refresh }).subscribe({ error: () => undefined });
    }
    localStorage.removeItem(this.accessKey);
    localStorage.removeItem(this.refreshKey);
    localStorage.removeItem(this.userKey);
    this.authState.next(false);
    this.router.navigate(['/admin/login']);
  }

  refreshToken(): Observable<{ access: string; refresh?: string }> {
    return this.http
      .post<{ access: string; refresh?: string }>(`${environment.apiUrl}/auth/refresh/`, {
        refresh: this.getRefreshToken(),
      })
      .pipe(
        tap((response) => {
          localStorage.setItem(this.accessKey, response.access);
          if (response.refresh) {
            localStorage.setItem(this.refreshKey, response.refresh);
          }
          this.authState.next(true);
        }),
      );
  }

  getAccessToken(): string | null {
    return localStorage.getItem(this.accessKey);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.refreshKey);
  }

  isAuthenticated(): boolean {
    return Boolean(this.getAccessToken());
  }
}


