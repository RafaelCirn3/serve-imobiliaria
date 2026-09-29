import { Property, PropertyType } from './api.models';

export const PROPERTY_TYPES: ReadonlyArray<{ value: PropertyType; label: string }> = [
  { value: 'apartamento', label: 'Apartamento' },
  { value: 'terreno', label: 'Área/Terreno' },
  { value: 'casa', label: 'Casa' },
  { value: 'condominio', label: 'Condomínio fechado' },
  { value: 'flat', label: 'Flat' },
  { value: 'cobertura', label: 'Cobertura' },
  { value: 'comercial', label: 'Comercial' },
];

export const SERVICE_CITIES = ['João Pessoa', 'Cabedelo', 'Bananeiras'] as const;

export function propertyTypeLabel(type: PropertyType): string {
  return PROPERTY_TYPES.find((option) => option.value === type)?.label ?? type;
}

export function propertyArea(property: Property): { value: string | number | null | undefined; label: string } {
  if (property.tipo === 'terreno' || property.area_privativa == null || property.area_privativa === '') {
    return { value: property.area_total, label: 'Área total' };
  }
  return { value: property.area_privativa, label: 'Área privativa' };
}
