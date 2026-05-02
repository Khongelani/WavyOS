import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../core/services/auth.service';

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, CommonModule],
  template: `
    <div class="app-shell">
      <!-- Sidebar (desktop) -->
      <nav class="sidebar" [class.open]="sidebarOpen">
        <div class="sidebar-logo">
          <span class="logo-mark">W</span>
          <span class="logo-text">WavyOS</span>
        </div>

        <ul class="nav-list">
          @for (item of navItems; track item.path) {
            <li>
              <a [routerLink]="item.path" routerLinkActive="active"
                 class="nav-link" (click)="sidebarOpen = false">
                <span class="material-icons nav-icon">{{ item.icon }}</span>
                <span class="nav-label">{{ item.label }}</span>
              </a>
            </li>
          }
        </ul>

        <div class="sidebar-footer">
          <button class="nav-link logout-btn" (click)="logout()">
            <span class="material-icons nav-icon">logout</span>
            <span class="nav-label">Sign Out</span>
          </button>
        </div>
      </nav>

      <!-- Mobile overlay -->
      @if (sidebarOpen) {
        <div class="overlay" (click)="sidebarOpen = false"></div>
      }

      <!-- Main content -->
      <div class="main-wrapper">
        <!-- Mobile topbar -->
        <header class="topbar">
          <button class="menu-btn" (click)="sidebarOpen = !sidebarOpen">
            <span class="material-icons">menu</span>
          </button>
          <span class="topbar-title">WavyOS</span>
          <div class="topbar-spacer"></div>
        </header>

        <main class="main-content">
          <router-outlet />
        </main>
      </div>

      <!-- Mobile bottom nav -->
      <nav class="bottom-nav">
        @for (item of mobileNavItems; track item.path) {
          <a [routerLink]="item.path" routerLinkActive="active" class="bottom-nav-item">
            <span class="material-icons">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </a>
        }
      </nav>
    </div>
  `,
  styleUrl: './layout.component.scss',
})
export class LayoutComponent {
  sidebarOpen = false;

  navItems: NavItem[] = [
    { path: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
    { path: '/companies', label: 'Companies', icon: 'business' },
    { path: '/pipeline', label: 'Pipeline', icon: 'view_kanban' },
    { path: '/contacts', label: 'Contacts', icon: 'contacts' },
    { path: '/research', label: 'Research', icon: 'search' },
    { path: '/signal-briefs', label: 'Signal Briefs', icon: 'analytics' },
    { path: '/outreach', label: 'Outreach', icon: 'send' },
    { path: '/sprint', label: 'Sprint Board', icon: 'rocket_launch' },
    { path: '/review', label: 'Weekly Review', icon: 'event_note' },
    { path: '/tasks', label: 'Tasks', icon: 'check_circle' },
    { path: '/settings', label: 'Settings', icon: 'settings' },
  ];

  mobileNavItems: NavItem[] = [
    { path: '/dashboard', label: 'Home', icon: 'dashboard' },
    { path: '/pipeline', label: 'Pipeline', icon: 'view_kanban' },
    { path: '/sprint', label: 'Sprint', icon: 'rocket_launch' },
    { path: '/tasks', label: 'Tasks', icon: 'check_circle' },
    { path: '/settings', label: 'More', icon: 'settings' },
  ];

  constructor(private auth: AuthService) {}

  logout(): void {
    this.auth.logout();
  }
}
