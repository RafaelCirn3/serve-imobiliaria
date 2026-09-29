import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '@env/environment';

export interface PostalAddress { cep: string; localidade: string; uf: string; bairro: string; logradouro: string; complemento?: string; }

@Injectable({ providedIn: 'root' })
export class LocationService {
  private readonly http = inject(HttpClient);
  private readonly url = `${environment.apiUrl}/localizacao`;
  cep(cep: string): Observable<PostalAddress> { return this.http.get<PostalAddress>(`${this.url}/cep/`, { params: { cep } }); }
  addresses(cidade: string, logradouro: string): Observable<PostalAddress[]> {
    return this.http.get<PostalAddress[]>(`${this.url}/enderecos/`, { params: { cidade, logradouro } });
  }
  neighborhoods(cidade: string): Observable<string[]> { return this.http.get<string[]>(`${this.url}/bairros/`, { params: { cidade } }); }
  streets(cidade: string, bairro: string): Observable<string[]> { return this.http.get<string[]>(`${this.url}/ruas/`, { params: { cidade, bairro } }); }
  mapConfig(): Observable<{ tile_url: string; attribution: string }> {
    return this.http.get<{ tile_url: string; attribution: string }>(`${this.url}/mapa-config/`);
  }
  geocode(payload: Record<string, unknown>): Observable<{ latitude: number; longitude: number; localizacao_exata: boolean; descricao: string }> {
    return this.http.post<{ latitude: number; longitude: number; localizacao_exata: boolean; descricao: string }>(`${this.url}/geocodificar/`, payload);
  }
}
