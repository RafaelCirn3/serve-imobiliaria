import { Routes } from '@angular/router';
import { adminAuthGuard } from './core/guards/admin-auth.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./features/public/home/home.component').then((m) => m.HomeComponent),
  },
  {
    path: 'imoveis',
    loadComponent: () => import('./features/public/properties/properties.component').then((m) => m.PropertiesComponent),
  },
  {
    path: 'imoveis/:slug',
    loadComponent: () => import('./features/public/property-detail/property-detail.component').then((m) => m.PropertyDetailComponent),
  },
  {
    path: 'sobre',
    loadComponent: () => import('./features/public/about/about.component').then((m) => m.AboutComponent),
  },
  {
    path: 'contato',
    loadComponent: () => import('./features/public/contact/contact.component').then((m) => m.ContactComponent),
  },
  {
    path: 'admin/login',
    loadComponent: () => import('./features/admin/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'admin',
    canActivate: [adminAuthGuard],
    loadComponent: () => import('./features/admin/layout/admin-layout.component').then((m) => m.AdminLayoutComponent),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      { path: 'customizacao', canDeactivate: [(component: {dirty:boolean}) => !component.dirty || confirm('Sair sem salvar as alterações de customização?')], loadComponent: () => import('./features/admin/customization/customization.component').then(m => m.CustomizationComponent) },
      { path: 'dashboard', loadComponent: () => import('./features/admin/dashboard/dashboard.component').then((m) => m.DashboardComponent) },
      { path: 'imoveis', loadComponent: () => import('./features/admin/properties/admin-properties.component').then((m) => m.AdminPropertiesComponent) },
      { path: 'imoveis/novo', loadComponent: () => import('./features/admin/property-form/property-form.component').then((m) => m.PropertyFormComponent) },
      { path: 'imoveis/:id/editar', loadComponent: () => import('./features/admin/property-form/property-form.component').then((m) => m.PropertyFormComponent) },
      { path: 'leads', loadComponent: () => import('./features/admin/leads/admin-leads.component').then((m) => m.AdminLeadsComponent) },
      { path: 'carrosseis', pathMatch: 'full', redirectTo: 'customizacao' },
      { path: 'section-images', pathMatch: 'full', redirectTo: 'customizacao' },
      { path: 'home-content', pathMatch: 'full', redirectTo: 'customizacao' },
      { path: 'banners', pathMatch: 'full', redirectTo: 'customizacao' },
      { path: 'regioes', pathMatch: 'full', redirectTo: 'customizacao' },
    ],
  },
  { path: '**', redirectTo: '' },
];


