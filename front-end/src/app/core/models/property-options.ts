import { Property, PropertyType } from './api.models';

export const PROPERTY_TYPES: ReadonlyArray<{ value: PropertyType; label: string }> = [
  { value: 'apartamento', label: 'Apartamento' },
  { value: 'terreno', label: 'Área/Terreno' },
  { value: 'casa', label: 'Casa' },
  { value: 'condominio', label: 'Condomínio fechado' },
  { value: 'flat', label: 'Flat' },
  { value: 'cobertura', label: 'Cobertura' },
  { value: 'comercial', label: 'Comercial' },
  { value: 'lancamento', label: 'Lançamento' },
  { value: 'em_construcao', label: 'Em construção' },
  { value: 'novo', label: 'Novo' },
  { value: 'pronto', label: 'Pronto' },
];

export const SERVICE_CITIES = ['João Pessoa', 'Cabedelo', 'Bananeiras'] as const;

export function normalizedLocation(value: unknown): string {
  return String(value || '').trim().replace(/\s+/g, ' ').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
}

export function propertyTypeLabel(type: PropertyType): string {
  return PROPERTY_TYPES.find((option) => option.value === type)?.label ?? type;
}

export function parkingLabel(property: Property): string {
  if (property.vagas_min && property.vagas_max && property.vagas_min !== property.vagas_max) {
    return `${property.vagas_min} a ${property.vagas_max} vagas`;
  }
  return property.vagas_rotativas
    ? (property.vagas > 0 ? `${property.vagas} vaga(s) rotativa(s)` : 'Vagas rotativas')
    : `${property.vagas} vagas`;
}

export function propertyArea(property: Property): { value: string | number | null | undefined; label: string } {
  if (!Number(property.area_privativa) && !Number(property.area_total) && Number(property.area_informada) > 0) {
    return { value: property.area_informada, label: 'Área' };
  }
  if (property.tipo === 'terreno' || property.area_privativa == null || property.area_privativa === '') {
    return { value: property.area_total, label: 'Área total' };
  }
  return { value: property.area_privativa, label: 'Área privativa' };
}
