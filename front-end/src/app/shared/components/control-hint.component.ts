import { Component, Input } from '@angular/core';
import { AbstractControl } from '@angular/forms';
@Component({
  selector: 'app-control-hint', standalone: true,
  template: `@if (control.invalid && (control.touched || control.dirty)) { <small class="invalid">! {{ message }}</small> } @else if (filled && control.valid) { <small class="complete">✓ Preenchido</small> } @else { <small class="pending">{{ required ? 'Obrigatório' : 'Opcional' }}</small> }`,
  styles: [`small { display: block; font-size: 12px; line-height: 1.5; font-weight: 500; } .invalid { color: #a02727; } .complete { color: #286747; } .pending { color: #69747d; } :host-context(app-sale-dialog) .complete { color:#91d2ab; } :host-context(app-sale-dialog) .pending { color:#b8b8b8; } :host-context(app-sale-dialog) .invalid { color:#ffb4b4; }`],
})
export class ControlHintComponent {
  @Input({required:true}) control!: AbstractControl;
  @Input() required = false;
  get filled(): boolean { return this.control.value !== null && this.control.value !== undefined && String(this.control.value).trim() !== ''; }
  get message(): string {
    if (this.control.hasError('server')) return String(this.control.getError('server'));
    if (this.control.hasError('required')) return 'Preencha este campo.';
    if (this.control.hasError('min')) return 'Use um valor igual ou maior que zero.';
    if (this.control.hasError('maxlength')) return 'O texto excede o limite do campo.';
    return 'Confira o valor informado.';
  }
}
