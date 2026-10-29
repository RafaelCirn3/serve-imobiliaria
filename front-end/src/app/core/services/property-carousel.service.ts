import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '@env/environment';
import { PropertyCarousel, PaginatedResponse } from '@core/models/api.models';

@Injectable({providedIn:'root'})
export class PropertyCarouselService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/admin/carrosseis/`;
  list(admin = false) { return this.http.get<PaginatedResponse<PropertyCarousel>>(`${environment.apiUrl}/${admin ? 'admin/' : ''}carrosseis/`); }
  create(v: Partial<PropertyCarousel>) { return this.http.post<PropertyCarousel>(this.base,v); }
  update(id:number,v:Partial<PropertyCarousel>) { return this.http.patch<PropertyCarousel>(`${this.base}${id}/`,v); }
  remove(id:number) { return this.http.delete<void>(`${this.base}${id}/`); }
}
