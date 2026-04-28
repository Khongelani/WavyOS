import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService, DashboardStats } from '../../core/services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="page">
      <div class="page-header">
        <h2>Dashboard</h2>
        <span class="subtitle">Command overview</span>
      </div>

      @if (loading) {
        <div class="loading">Loading stats...</div>
      } @else if (stats) {
        <div class="stat-grid">
          <div class="stat-card">
            <div class="stat-label">Companies</div>
            <div class="stat-value">{{ stats.total_companies }}</div>
            <div class="stat-sub">in system</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Researched</div>
            <div class="stat-value accent">{{ stats.companies_researched }}</div>
            <div class="stat-sub">with reports</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Contacts</div>
            <div class="stat-value">{{ stats.contacts_added }}</div>
            <div class="stat-sub">added</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Briefs</div>
            <div class="stat-value">{{ stats.briefs_generated }}</div>
            <div class="stat-sub">generated</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Outreach Drafts</div>
            <div class="stat-value">{{ stats.outreach_drafts }}</div>
            <div class="stat-sub">created</div>
          </div>
          <div class="stat-card highlight">
            <div class="stat-label">Calls Booked</div>
            <div class="stat-value accent">{{ stats.calls_booked }}</div>
            <div class="stat-sub">pipeline stage 6</div>
          </div>
        </div>

        <!-- Today's tasks -->
        <div class="section">
          <h3 class="section-title">Today's Actions</h3>
          @if (stats.today_tasks.length === 0) {
            <div class="empty-state">No pending tasks due today.</div>
          } @else {
            <div class="task-list">
              @for (task of stats.today_tasks; track task.id) {
                <div class="task-row">
                  <span class="task-dot pending"></span>
                  <span class="task-desc">{{ task.description }}</span>
                  @if (task.due_date) {
                    <span class="task-due">{{ task.due_date | date:'MMM d' }}</span>
                  }
                  <a [routerLink]="['/tasks']" class="task-link">View →</a>
                </div>
              }
            </div>
          }
        </div>

        <!-- Quick actions -->
        <div class="section">
          <h3 class="section-title">Quick Actions</h3>
          <div class="quick-actions">
            <a routerLink="/companies" class="action-card">
              <span class="material-icons">add_business</span>
              <span>Add Company</span>
            </a>
            <a routerLink="/research" class="action-card">
              <span class="material-icons">search</span>
              <span>Run Research</span>
            </a>
            <a routerLink="/pipeline" class="action-card">
              <span class="material-icons">view_kanban</span>
              <span>View Pipeline</span>
            </a>
            <a routerLink="/contacts" class="action-card">
              <span class="material-icons">person_add</span>
              <span>Add Contact</span>
            </a>
          </div>
        </div>
      }
    </div>
  `,
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  stats: DashboardStats | null = null;
  loading = true;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getDashboardStats().subscribe({
      next: (s) => {
        this.stats = s;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}
