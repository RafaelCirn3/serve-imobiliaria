import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '@env/environment';
import { PaginatedResponse, Property, PropertyFilters, PropertyImage, PropertyPayload } from '../models/api.models';
import { toHttpParams } from './api-utils';

@Injectable({ providedIn: 'root' })
export class PropertyService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/imoveis`;
  private readonly adminUrl = `${environment.apiUrl}/admin/imoveis`;

  listPublicProperties(filters: PropertyFilters = {}): Observable<PaginatedResponse<Property>> {
    return this.http.get<PaginatedResponse<Property>>(`${this.baseUrl}/`, { params: toHttpParams(filters) });
  }

  getPropertyBySlug(slug: string): Observable<Property> {
    return this.http.get<Property>(`${this.baseUrl}/${slug}/`);
  }

  getFeaturedProperties(): Observable<PaginatedResponse<Property>> {
    return this.http.get<PaginatedResponse<Property>>(`${this.baseUrl}/destaques/`);
  }

  searchProperties(query: string, filters: PropertyFilters = {}): Observable<PaginatedResponse<Property>> {
    return this.http.get<PaginatedResponse<Property>>(`${this.baseUrl}/busca/`, {
      params: toHttpParams({ ...filters, q: query }),
    });
  }

  listAdminProperties(filters: PropertyFilters = {}): Observable<PaginatedResponse<Property>> {
    return this.http.get<PaginatedResponse<Property>>(`${this.adminUrl}/`, { params: toHttpParams(filters) });
  }

  getAdminProperty(id: number | string): Observable<Property> {
    return this.http.get<Property>(`${this.adminUrl}/${id}/`);
  }

  createProperty(payload: PropertyPayload): Observable<Property> {
    return this.http.post<Property>(`${this.adminUrl}/`, payload);
  }

  updateProperty(id: number | string, payload: Partial<PropertyPayload>): Observable<Property> {
    return this.http.patch<Property>(`${this.adminUrl}/${id}/`, payload);
  }

  deleteProperty(id: number): Observable<void> {
    return this.http.delete<void>(`${this.adminUrl}/${id}/`);
  }

  uploadPropertyImages(propertyId: number | string, files: File[], data: Record<string, string | number | boolean> = {}): Observable<PropertyImage[]> {
    const formData = new FormData();
    files.forEach((file) => formData.append('imagens', file));
    Object.entries(data).forEach(([key, value]) => formData.append(key, String(value)));
    return this.http.post<PropertyImage[]>(`${this.adminUrl}/${propertyId}/imagens/`, formData);
  }

  updatePropertyImage(propertyId: number | string, imageId: number, payload: Partial<PropertyImage>): Observable<PropertyImage> {
    return this.http.patch<PropertyImage>(`${this.adminUrl}/${propertyId}/imagens/${imageId}/`, payload);
  }

  deletePropertyImage(propertyId: number | string, imageId: number): Observable<void> {
    return this.http.delete<void>(`${this.adminUrl}/${propertyId}/imagens/${imageId}/`);
  }
}
