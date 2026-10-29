import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '@env/environment';
import { PaginatedResponse, SectionImage } from '@core/models/api.models';

@Injectable({providedIn: 'root'})
export class SectionImageService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/admin/section-images/`;
  list(admin = false) { return this.http.get<PaginatedResponse<SectionImage>>(`${environment.apiUrl}/${admin ? 'admin/' : ''}section-images/`); }
  create(data: FormData) { return this.http.post<SectionImage>(this.base, data); }
  update(id: number, data: FormData) { return this.http.patch<SectionImage>(`${this.base}${id}/`, data); }
  remove(id: number) { return this.http.delete<void>(`${this.base}${id}/`); }
}
