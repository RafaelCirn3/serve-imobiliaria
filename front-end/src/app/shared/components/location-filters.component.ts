import { Component, DestroyRef, Input, OnInit, inject } from '@angular/core';
import { FormGroup, ReactiveFormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, combineLatest, of, startWith, switchMap } from 'rxjs';
import { LocationService } from '@core/services/location.service';
import { SERVICE_CITIES, normalizedLocation } from '@core/models/property-options';

@Component({
  selector: 'app-location-filters', standalone: true, imports: [ReactiveFormsModule],
  template: `
    <div class="location-fields" [class.compact]="compact" [formGroup]="form">
      <label>Cidade<select formControlName="cidade" (change)="cityChanged()"><option value="">Todas as cidades</option>
        @for (city of cities; track city) { <option [value]="city">{{ city }}</option> }
      </select></label>
      <label>Bairro<select formControlName="bairro" (change)="neighborhoodChanged()"><option value="">{{ loadingNeighborhoods ? 'Carregando…' : 'Todos os bairros' }}</option>
        @if (currentNeighborhood && !neighborhoods.includes(currentNeighborhood)) { <option [value]="currentNeighborhood">{{ currentNeighborhood }}</option> }
        @for (neighborhood of neighborhoods; track neighborhood) { <option [value]="neighborhood">{{ neighborhood }}</option> }
      </select></label>
      <label>Rua<select formControlName="logradouro"><option value="">{{ loadingStreets ? 'Carregando…' : 'Todas as ruas' }}</option>
        @if (currentStreet && !streets.includes(currentStreet)) { <option [value]="currentStreet">{{ currentStreet }}</option> }
        @for (street of streets; track street) { <option [value]="street">{{ street }}</option> }
      </select></label>
    </div>
    @if (error) { <p class="error" role="alert">{{ error }}</p> }
  `,
  styles: [`
    :host { display: block; min-width: 0; } .location-fields { display: grid; gap: 14px; }
    label { display: grid; gap: 7px; min-width: 0; color: #b8b8b8; font-size: .86rem; font-weight: 800; }
    select { width: 100%; min-width: 0; min-height: 42px; padding: 0 10px; color: #f5f5f5; background: #12161a; border: 1px solid #30363d; border-radius: 8px; }
    select:disabled { opacity: .55; } .error { color: #ffb4b4; font-size: .8rem; } :focus-visible { outline: 2px solid white; }
    .compact { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
    @media(max-width:560px) { .compact { grid-template-columns: 1fr; } }
  `],
})
export class LocationFiltersComponent implements OnInit {
  @Input({ required: true }) form!: FormGroup;
  @Input() compact = false;
  private readonly locations = inject(LocationService);
  private readonly destroyRef = inject(DestroyRef);
  readonly cities = SERVICE_CITIES;
  neighborhoods: string[] = []; streets: string[] = [];
  loadingNeighborhoods = false; loadingStreets = false; error = '';
  get currentNeighborhood(): string { return this.form.get('bairro')!.value; }
  get currentStreet(): string { return this.form.get('logradouro')!.value; }
  ngOnInit(): void {
    const city = this.form.get('cidade')!;
    const neighborhood = this.form.get('bairro')!;
    const street = this.form.get('logradouro')!;
    city.valueChanges.pipe(startWith(city.value), switchMap((value) => {
      const canonical = this.cities.find((candidate) => normalizedLocation(candidate) === normalizedLocation(value));
      if (canonical && canonical !== value) city.setValue(canonical, { emitEvent: false });
      this.error = ''; this.neighborhoods = []; this.loadingNeighborhoods = Boolean(value);
      if (!value) { neighborhood.disable({ emitEvent: false }); return of([]); }
      neighborhood.enable({ emitEvent: false });
      return this.locations.neighborhoods(value).pipe(catchError(() => { this.error = 'Não foi possível carregar os bairros. Tente selecionar a cidade novamente.'; return of([]); }));
    }), takeUntilDestroyed(this.destroyRef)).subscribe((values) => { this.neighborhoods = values; this.loadingNeighborhoods = false; });
    combineLatest([city.valueChanges.pipe(startWith(city.value)), neighborhood.valueChanges.pipe(startWith(neighborhood.value))]).pipe(
      switchMap(([cityValue, neighborhoodValue]) => {
        this.streets = []; this.loadingStreets = Boolean(cityValue && neighborhoodValue);
        if (!cityValue || !neighborhoodValue) { street.disable({ emitEvent: false }); return of([]); }
        street.enable({ emitEvent: false });
        return this.locations.streets(cityValue, neighborhoodValue).pipe(catchError(() => { this.error = 'Não foi possível carregar as ruas. Você pode buscar pela cidade e pelo bairro.'; return of([]); }));
      }), takeUntilDestroyed(this.destroyRef),
    ).subscribe((values) => { this.streets = values; this.loadingStreets = false; });
  }
  cityChanged(): void { this.form.patchValue({ bairro: '', logradouro: '' }); }
  neighborhoodChanged(): void { this.form.patchValue({ logradouro: '' }); }
}
