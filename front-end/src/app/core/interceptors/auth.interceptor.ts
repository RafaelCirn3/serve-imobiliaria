import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { environment } from '@env/environment';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);
  const token = auth.getAccessToken();
  const shouldAttachToken = token && request.url.startsWith(environment.apiUrl);

  const authRequest = shouldAttachToken
    ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : request;

  return next(authRequest).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && auth.getRefreshToken() && !request.url.includes('/auth/refresh/')) {
        return auth.refreshToken().pipe(
          catchError((refreshError) => {
            auth.logout();
            return throwError(() => refreshError);
          }),
          switchMap(() => {
            const refreshedToken = auth.getAccessToken();
            const retryRequest = refreshedToken
              ? request.clone({ setHeaders: { Authorization: `Bearer ${refreshedToken}` } })
              : request;
            return next(retryRequest);
          }),
        );
      }

      return throwError(() => error);
    }),
  );
};


