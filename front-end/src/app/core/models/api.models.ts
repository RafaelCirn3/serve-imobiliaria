export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type PropertyStatus = 'rascunho' | 'publicado' | 'vendido' | 'alugado' | 'inativo';
export type PropertyType = 'apartamento' | 'casa' | 'cobertura' | 'terreno' | 'comercial' | 'condominio' | 'flat';
export type PropertyPurpose = 'venda' | 'aluguel';
export type LeadStatus = 'novo' | 'em_atendimento' | 'finalizado' | 'descartado';

export interface PropertyImage {
  id: number;
  imagem: string;
  legenda: string;
  ordem: number;
  imagem_capa: boolean;
  criado_em?: string;
}

export interface Property {
  id: number;
  titulo: string;
  slug: string;
  descricao: string;
  tipo: PropertyType;
  finalidade: PropertyPurpose;
  status?: PropertyStatus;
  destaque: boolean;
  valor: string | number;
  valor_condominio?: string | number | null;
  valor_iptu?: string | number | null;
  regiao?: number | null;
  cidade: string;
  bairro: string;
  endereco?: string;
  cep?: string;
  uf?: string;
  logradouro?: string;
  numero?: string;
  complemento?: string;
  latitude?: string | number | null;
  longitude?: string | number | null;
  localizacao_exata?: boolean;
  area_total?: string | number | null;
  area_privativa?: string | number | null;
  quartos: number;
  suites: number;
  banheiros: number;
  vagas: number;
  aceita_financiamento: boolean;
  mobiliado: boolean;
  possui_piscina: boolean;
  possui_academia: boolean;
  possui_elevador: boolean;
  possui_area_gourmet: boolean;
  descricao_seo?: string;
  titulo_seo?: string;
  criado_em?: string;
  atualizado_em?: string;
  publicado_em?: string | null;
  imagens: PropertyImage[];
}

export type PropertyPayload = Omit<
  Property,
  'id' | 'slug' | 'criado_em' | 'atualizado_em' | 'publicado_em' | 'imagens'
>;

export interface PropertyFilters {
  visualizacao?: 'lista' | 'mapa';
  cidade?: string;
  bairro?: string;
  logradouro?: string;
  cep?: string;
  tipo?: string;
  finalidade?: string;
  valor_min?: string | number;
  valor_max?: string | number;
  quartos?: string | number;
  suites?: string | number;
  vagas?: string | number;
  area_min?: string | number;
  area_max?: string | number;
  area_total_min?: string | number;
  area_total_max?: string | number;
  destaque?: boolean | string;
  status?: string;
  ordering?: string;
  search?: string;
  page?: number;
}

export interface MapProperty {
  id: number; titulo: string; slug: string; valor: string | number; cidade: string; bairro: string;
  latitude?: string | number | null; longitude?: string | number | null; localizacao_exata?: boolean;
  foto?: string | null; imagens?: PropertyImage[];
}

export interface MapResponse {
  count: number; geolocalizados: number; sem_coordenadas: number; limite: number; truncado: boolean; results: MapProperty[];
}

export interface Lead {
  id: number;
  imovel?: number | null;
  imovel_titulo?: string;
  nome: string;
  email: string;
  telefone: string;
  mensagem: string;
  origem: 'formulario' | 'whatsapp' | 'botao_contato' | 'venda_imovel';
  dados_imovel?: Record<string, string | number | null>;
  notificacao_status?: 'nao_aplicavel' | 'pendente' | 'enviado' | 'falhou';
  notificacao_tentativas?: number;
  status?: LeadStatus;
  criado_em?: string;
}

export interface Region {
  id: number;
  nome: string;
  cidade: string;
  descricao: string;
  imagem?: string | null;
  ativo: boolean;
}

export interface RegionPayload {
  nome?: string;
  cidade?: string;
  descricao?: string;
  imagem?: File | null;
  ativo?: boolean;
}

export interface Banner {
  id: number;
  titulo: string;
  subtitulo: string;
  imagem: string;
  botao_texto: string;
  botao_link: string;
  ativo: boolean;
  ordem: number;
}

export interface BannerPayload {
  titulo?: string;
  subtitulo?: string;
  imagem?: File | null;
  botao_texto?: string;
  botao_link?: string;
  ativo?: boolean;
  ordem?: number;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: {
    id: number;
    nome: string;
    email: string;
    is_staff: boolean;
    is_superuser: boolean;
  };
}


