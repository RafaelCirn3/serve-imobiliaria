import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '@env/environment';
import { Banner, BannerPayload, PaginatedResponse } from '../models/api.models';
import { toFormData } from './api-utils';

@Injectable({ providedIn: 'root' })
export class BannerService {
  private readonly http = inject(HttpClient);

  listBanners(admin = false): Observable<PaginatedResponse<Banner>> {
    return this.http.get<PaginatedResponse<Banner>>(`${environment.apiUrl}/${admin ? 'admin/' : ''}banners/`);
  }

  createBanner(payload: BannerPayload): Observable<Banner> {
    return this.http.post<Banner>(`${environment.apiUrl}/admin/banners/`, this.toPayload(payload));
  }

  updateBanner(id: number, payload: BannerPayload): Observable<Banner> {
    return this.http.patch<Banner>(`${environment.apiUrl}/admin/banners/${id}/`, this.toPayload(payload));
  }

  deleteBanner(id: number): Observable<void> {
    return this.http.delete<void>(`${environment.apiUrl}/admin/banners/${id}/`);
  }

  private toPayload(payload: BannerPayload): BannerPayload | FormData {
    return payload.imagem instanceof File ? toFormData(payload as Record<string, unknown>) : payload;
  }
}
