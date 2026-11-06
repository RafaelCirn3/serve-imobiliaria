import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '@env/environment';
import { Lead, LeadStatus, PaginatedResponse } from '../models/api.models';
import { toHttpParams } from './api-utils';

@Injectable({ providedIn: 'root' })
export class LeadService {
  private readonly http = inject(HttpClient);

  offerProperty(payload: Record<string, unknown>, files: File[] = []): Observable<{ id: number; notificacao_status: string }> {
    const body = new FormData();
    Object.entries(payload).forEach(([key, value]) => { if (value !== null && value !== undefined) body.append(key, String(value)); });
    files.forEach(file => body.append('fotos', file));
    return this.http.post<{ id: number; notificacao_status: string }>(`${environment.apiUrl}/leads/venda-imovel/`, body);
  }

  retryNotification(id: number): Observable<Lead> {
    return this.http.post<Lead>(`${environment.apiUrl}/admin/leads/${id}/reenviar-notificacao/`, {});
  }

  createLead(payload: Partial<Lead>): Observable<Lead> {
    return this.http.post<Lead>(`${environment.apiUrl}/leads/`, payload);
  }

  listAdminLeads(filters: Record<string, unknown> = {}): Observable<PaginatedResponse<Lead>> {
    return this.http.get<PaginatedResponse<Lead>>(`${environment.apiUrl}/admin/leads/`, { params: toHttpParams(filters) });
  }

  updateLeadStatus(id: number, status: LeadStatus): Observable<Lead> {
    return this.http.patch<Lead>(`${environment.apiUrl}/admin/leads/${id}/`, { status });
  }
}


