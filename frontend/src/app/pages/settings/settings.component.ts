import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page">
      <div class="page-header">
        <h2>Settings</h2>
      </div>

      <!-- Health status -->
      <div class="section-card">
        <h3>App Health</h3>
        @if (health) {
          <div class="health-grid">
            <div class="health-item">
              <span class="indicator" [class]="dotClass(health.api)"></span>
              <span class="health-label">API</span>
              <span class="health-val mono">{{ health.api }}</span>
            </div>
            <div class="health-item">
              <span class="indicator" [class]="dotClass(health.database)"></span>
              <span class="health-label">Database</span>
              <span class="health-val mono">{{ health.database }}</span>
            </div>
            <div class="health-item">
              <span class="indicator" [class]="dotClass(health.ai)"></span>
              <span class="health-label">AI / OpenAI</span>
              <span class="health-val mono">{{ health.ai }}</span>
            </div>
          </div>
        } @else {
          <div class="loading">Checking health...</div>
        }
      </div>

      <!-- Owner profile -->
      <div class="section-card">
        <h3>Owner Profile</h3>
        <div class="profile-row">
          <span class="label">Email</span>
          <span class="value mono">{{ ownerEmail }}</span>
        </div>
        <div class="profile-row">
          <span class="label">Credentials</span>
          <span class="value muted">Configured via .env file</span>
        </div>
      </div>

      <!-- OpenAI -->
      <div class="section-card">
        <h3>OpenAI Integration</h3>
        <div class="profile-row">
          <span class="label">API Key</span>
          @if (health?.ai !== 'demo_mode') {
            <span class="value status-ok">● Configured</span>
          } @else {
            <span class="value status-warn">● Not configured — running in demo mode</span>
          }
        </div>
        <p class="hint-text">To configure, set OPENAI_API_KEY in your .env file and restart the backend.</p>
      </div>

      <!-- Export -->
      <div class="section-card">
        <h3>Export Data</h3>
        <div class="export-grid">
          <button class="export-btn" (click)="exportCsv('companies')">
            <span class="material-icons">download</span>
            Export Companies
          </button>
          <button class="export-btn" (click)="exportCsv('contacts')">
            <span class="material-icons">download</span>
            Export Contacts
          </button>
          <button class="export-btn" (click)="exportCsv('tasks')">
            <span class="material-icons">download</span>
            Export Tasks
          </button>
        </div>
      </div>

      <!-- Danger zone -->
      <div class="section-card danger-zone">
        <h3>Danger Zone</h3>
        <p class="hint-text">Remove all demo / seed data generated at startup. This cannot be undone.</p>
        @if (!confirmClear) {
          <button class="btn-danger" (click)="confirmClear = true">Clear Demo Data</button>
        } @else {
          <div class="confirm-row">
            <span>Are you sure?</span>
            <button class="btn-ghost" (click)="confirmClear = false">Cancel</button>
            <button class="btn-danger" (click)="clearDemo()">Yes, clear demo data</button>
          </div>
        }
        @if (clearMsg) {
          <div class="success-msg">{{ clearMsg }}</div>
        }
      </div>

      <!-- Sign out -->
      <div class="section-card">
        <button class="btn-ghost logout-btn" (click)="logout()">
          <span class="material-icons">logout</span> Sign Out
        </button>
      </div>
    </div>
  `,
  styleUrl: './settings.component.scss',
})
export class SettingsComponent implements OnInit {
  health: { api: string; database: string; ai: string } | null = null;
  confirmClear = false;
  clearMsg = '';
  ownerEmail = '';

  constructor(private api: ApiService, private auth: AuthService) {}

  ngOnInit(): void {
    this.api.getHealth().subscribe(h => (this.health = h));
    const token = this.auth.getToken();
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        this.ownerEmail = payload.sub || '';
      } catch {}
    }
  }

  dotClass(status: string): string {
    if (status === 'ok' || status === 'configured') return 'dot-green';
    if (status === 'demo_mode') return 'dot-yellow';
    return 'dot-red';
  }

  exportCsv(entity: string): void {
    this.api.exportCsv(entity).subscribe(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${entity}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  clearDemo(): void {
    this.api.clearDemoData().subscribe({
      next: () => {
        this.clearMsg = 'Demo data cleared successfully.';
        this.confirmClear = false;
        setTimeout(() => (this.clearMsg = ''), 4000);
      },
      error: () => { this.clearMsg = 'Error clearing demo data.'; },
    });
  }

  logout(): void {
    this.auth.logout();
  }
}
