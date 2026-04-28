import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./shared/components/layout/layout.component').then(m => m.LayoutComponent),
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
      },
      {
        path: 'companies',
        loadComponent: () => import('./pages/companies/companies.component').then(m => m.CompaniesComponent),
      },
      {
        path: 'companies/:id',
        loadComponent: () => import('./pages/company-detail/company-detail.component').then(m => m.CompanyDetailComponent),
      },
      {
        path: 'research',
        loadComponent: () => import('./pages/research/research.component').then(m => m.ResearchComponent),
      },
      {
        path: 'signal-briefs',
        loadComponent: () => import('./pages/signal-briefs/signal-briefs.component').then(m => m.SignalBriefsComponent),
      },
      {
        path: 'contacts',
        loadComponent: () => import('./pages/contacts/contacts.component').then(m => m.ContactsComponent),
      },
      {
        path: 'outreach',
        loadComponent: () => import('./pages/outreach/outreach.component').then(m => m.OutreachComponent),
      },
      {
        path: 'pipeline',
        loadComponent: () => import('./pages/pipeline/pipeline.component').then(m => m.PipelineComponent),
      },
      {
        path: 'tasks',
        loadComponent: () => import('./pages/tasks/tasks.component').then(m => m.TasksComponent),
      },
      {
        path: 'settings',
        loadComponent: () => import('./pages/settings/settings.component').then(m => m.SettingsComponent),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
