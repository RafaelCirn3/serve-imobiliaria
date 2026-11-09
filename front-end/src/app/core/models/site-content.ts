import { Banner, HomeContent, PropertyCarousel, Region, SectionImage } from './api.models';
export type SitePage = 'general'|'home'|'properties'|'about'|'contact'|'detail';
export interface SectionSettings {id:string;visible:boolean;spacing:'original'|'compact'|'normal'|'wide';align:'original'|'left'|'center'|'right';tone:'original'|'dark'|'light';}
export type SiteConfig = Record<SitePage,Record<string,string>> & {layout:Record<SitePage,SectionSettings[]>};
export interface SiteDocument {revision:string;config:SiteConfig;home:HomeContent;banners:Banner[];section_images:SectionImage[];regions:Region[];carousels:PropertyCarousel[];}
export interface EditorField {key:string;label:string;type:string;max:number;}
export interface EditorDocument extends SiteDocument {fields:Record<SitePage,EditorField[]>;home_fields:EditorField[];sections:Record<SitePage,Record<string,string>>;}
