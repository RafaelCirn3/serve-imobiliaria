import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { environment } from '@env/environment';
import { HomeContent } from '@core/models/api.models';

@Injectable({ providedIn: 'root' })
export class HomeContentService {
  private readonly http = inject(HttpClient);
  load() { return this.http.get<HomeContent>(`${environment.apiUrl}/home-content/`); }
  update(payload: HomeContent) { return this.http.patch<HomeContent>(`${environment.apiUrl}/admin/home-content/`, payload); }
}
