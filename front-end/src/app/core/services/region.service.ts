import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '@env/environment';
import { PaginatedResponse, Region, RegionPayload } from '../models/api.models';
import { toFormData } from './api-utils';

@Injectable({ providedIn: 'root' })
export class RegionService {
  private readonly http = inject(HttpClient);

  listRegions(admin = false): Observable<PaginatedResponse<Region>> {
    return this.http.get<PaginatedResponse<Region>>(`${environment.apiUrl}/${admin ? 'admin/' : ''}regioes/`);
  }

  createRegion(payload: RegionPayload): Observable<Region> {
    return this.http.post<Region>(`${environment.apiUrl}/admin/regioes/`, this.toPayload(payload));
  }

  updateRegion(id: number, payload: RegionPayload): Observable<Region> {
    return this.http.patch<Region>(`${environment.apiUrl}/admin/regioes/${id}/`, this.toPayload(payload));
  }

  deleteRegion(id: number): Observable<void> {
    return this.http.delete<void>(`${environment.apiUrl}/admin/regioes/${id}/`);
  }

  private toPayload(payload: RegionPayload): RegionPayload | FormData {
    return payload.imagem instanceof File ? toFormData(payload as Record<string, unknown>) : payload;
  }
}
