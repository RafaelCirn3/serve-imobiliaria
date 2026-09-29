import { Component, DestroyRef, Input, OnInit, inject } from '@angular/core';
import { FormGroup, ReactiveFormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { EMPTY, catchError, distinctUntilChanged, map, merge, of, switchMap, timer } from 'rxjs';
import { LocationService, PostalAddress } from '@core/services/location.service';
import { SERVICE_CITIES, normalizedLocation } from '@core/models/property-options';

@Component({
  selector: 'app-address-editor', standalone: true, imports: [ReactiveFormsModule],
  template: `
    <div class="address-fields" [formGroup]="form">
      <label>CEP<input formControlName="cep" autocomplete="postal-code" maxlength="9" placeholder="00000-000"></label>
      <label>Cidade<input formControlName="cidade" maxlength="120" [attr.list]="listId + '-cities'"><datalist [id]="listId + '-cities'">@for (city of cities; track city) { <option [value]="city"></option> }</datalist></label>
      <label>UF<input formControlName="uf" maxlength="2"></label>
      <label>Bairro<input formControlName="bairro" maxlength="120"></label>
      <label class="full">Rua<input formControlName="logradouro" maxlength="255" placeholder="Digite a rua para consultar o CEP" autocomplete="off"></label>
      @if (addresses.length) {
        <div class="suggestions full"><span>Endereços encontrados:</span>
          @for (address of addresses; track address.cep + address.logradouro) {
            <button type="button" (click)="choose(address)">{{ address.logradouro }} · {{ address.bairro || 'Bairro não informado' }} · {{ address.cep }}</button>
          }
        </div>
      }
      <label>Número<input formControlName="numero" maxlength="30"></label>
      <label>Complemento<input formControlName="complemento" maxlength="120"></label>
      @if (message) { <p class="full hint" role="status">{{ message }}</p> }
      @if (outsideArea) { <p class="full hint">A SERVE atende João Pessoa, Cabedelo e Bananeiras/PB. Este endereço está fora da área de atendimento.</p> }
    </div>
  `,
  styles: [`
    :host { display: block; grid-column: 1 / -1; min-width: 0; } .address-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    label { display: grid; gap: 7px; font-size: .9rem; } input { width: 100%; min-width: 0; padding: 12px; border: 1px solid #ffffff30; border-radius: 8px; background: #111417; color: #f5f5f5; }
    .full { grid-column: 1 / -1; } .hint { color: #d4cba6; margin: 0; font-size: .85rem; line-height: 1.5; }
    .suggestions { display: grid; gap: 8px; max-height: 220px; overflow: auto; } .suggestions button { padding: 10px; text-align: left; color: white; background: #ffffff10; border: 1px solid #ffffff30; border-radius: 6px; }
    :focus-visible { outline: 2px solid white; outline-offset: 2px; } @media(max-width:560px) { .address-fields { grid-template-columns: 1fr; } }
  `],
})
export class AddressEditorComponent implements OnInit {
  @Input({ required: true }) form!: FormGroup;
  @Input() listId = 'address';
  private readonly locations = inject(LocationService);
  private readonly destroyRef = inject(DestroyRef);
  readonly cities = SERVICE_CITIES;
  addresses: PostalAddress[] = [];
  message = '';
  private addressRevision = 0;

  get outsideArea(): boolean {
    const city = String(this.form.get('cidade')?.value || '').trim();
    const uf = String(this.form.get('uf')?.value || '').toUpperCase();
    return Boolean(city && (!this.cities.some((item) => normalizedLocation(item) === normalizedLocation(city)) || (uf && uf !== 'PB')));
  }

  ngOnInit(): void {
    this.form.get('cep')!.valueChanges.pipe(
      map((value) => String(value || '').replace(/-/g, '').trim()), distinctUntilChanged(),
      switchMap((cep) => {
        this.message = '';
        this.addresses = [];
        const revision = ++this.addressRevision;
        if (!/^\d{8}$/.test(cep)) {
          if (cep) this.message = 'Use um CEP com oito dígitos ou preencha o endereço manualmente.';
          return EMPTY;
        }
        const snapshot = this.form.getRawValue();
        this.message = 'Consultando CEP…';
        return timer(400).pipe(switchMap(() => this.locations.cep(cep)), map((address) => ({ address, cep, snapshot, revision })), catchError((error) => {
          if (revision !== this.addressRevision) return EMPTY;
          this.message = error.status === 404 ? 'CEP não encontrado. Preencha o endereço manualmente.' : 'Consulta indisponível. Você pode preencher manualmente.';
          return EMPTY;
        }));
      }), takeUntilDestroyed(this.destroyRef),
    ).subscribe(({ address, cep, snapshot, revision }) => {
      if (revision !== this.addressRevision) return;
      if (String(this.form.get('cep')!.value).replace(/-/g, '').trim() !== cep) return;
      const values: Record<string, string> = { cidade: address.localidade || '', uf: address.uf || '', bairro: address.bairro || '', logradouro: address.logradouro || '' };
      const patch: Record<string, string> = {};
      for (const [key, value] of Object.entries(values)) {
        if (value && this.form.get(key)!.value === snapshot[key]) patch[key] = value;
      }
      this.form.patchValue(patch, { emitEvent: false });
      this.addressRevision++;
      this.addresses = [];
      this.message = 'Endereço consultado. Confira os dados e preencha o número. Campos ausentes podem ser informados manualmente.';
    });

    merge(this.form.get('logradouro')!.valueChanges, this.form.get('cidade')!.valueChanges, this.form.get('uf')!.valueChanges).pipe(
      map(() => ({ city: this.form.get('cidade')!.value, street: this.form.get('logradouro')!.value, uf: this.form.get('uf')!.value })),
      distinctUntilChanged((previous, current) => JSON.stringify(previous) === JSON.stringify(current)),
      switchMap(({ city, street, uf }) => {
        this.addresses = [];
        const revision = this.addressRevision;
        if (this.outsideArea || String(uf).toUpperCase() !== 'PB' || !city || String(street).trim().length < 3) return of({ addresses: [] as PostalAddress[], city, street, uf, revision });
        return timer(500).pipe(switchMap(() => this.locations.addresses(city, street)), map((addresses) => ({ addresses, city, street, uf, revision })), catchError(() => of({ addresses: [] as PostalAddress[], city, street, uf, revision })));
      }), takeUntilDestroyed(this.destroyRef),
    ).subscribe(({ addresses, city, street, uf, revision }) => {
      if (revision !== this.addressRevision) return;
      if (city !== this.form.get('cidade')!.value || street !== this.form.get('logradouro')!.value || uf !== this.form.get('uf')!.value) return;
      this.addresses = addresses.filter((address) => normalizedLocation(address.localidade) === normalizedLocation(city));
    });
  }

  choose(address: PostalAddress): void {
    this.addressRevision++;
    this.form.patchValue({ cep: address.cep, cidade: address.localidade, uf: address.uf, bairro: address.bairro, logradouro: address.logradouro }, { emitEvent: false });
    this.addresses = []; this.message = 'Endereço selecionado. Informe o número e confira os dados.';
  }
}
