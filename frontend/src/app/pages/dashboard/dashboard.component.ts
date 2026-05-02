import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService, DashboardStats } from '../../core/services/api.service';
import { ExecutionScoreboardComponent } from '../../shared/components/execution-scoreboard/execution-scoreboard.component';
import { AntiLoopAlertsComponent } from '../../shared/components/anti-loop-alerts/anti-loop-alerts.component';
import { FounderCommitmentComponent } from '../../shared/components/founder-commitment/founder-commitment.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    ExecutionScoreboardComponent,
    AntiLoopAlertsComponent,
    FounderCommitmentComponent,
  ],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Dashboard</h2>
          <span class="subtitle">Command overview</span>
        </div>
        <div class="header-actions">
          @if (isFriday) {
            <a routerLink="/review" class="btn-primary btn-sm">
              <span class="material-icons" style="font-size:14px">event_note</span>
              Weekly Review
            </a>
          }
        </div>
      </div>

      <!-- ① Execution Scoreboard — always first, never hidden -->
      <app-execution-scoreboard />

      <!-- ② Founder Commitment Banner (Monday only, dismissible) -->
      <app-founder-commitment />

      <!-- ③ Anti-Loop Alerts -->
      <app-anti-loop-alerts />

      <!-- ④ Existing dashboard content below -->
      @if (loading) {
        <div class="loading">Loading stats...</div>
      } @else if (stats) {
        <div class="stat-grid">
          <a class="stat-card" routerLink="/companies">
            <div class="stat-label">Companies</div>
            <div class="stat-value">{{ stats.total_companies }}</div>
            <div class="stat-sub">in system</div>
            <span class="stat-arrow">→</span>
          </a>
          <a class="stat-card" routerLink="/companies">
            <div class="stat-label">Researched</div>
            <div class="stat-value accent">{{ stats.companies_researched }}</div>
            <div class="stat-sub">with reports</div>
            <span class="stat-arrow">→</span>
          </a>
          <a class="stat-card" routerLink="/contacts">
            <div class="stat-label">Contacts</div>
            <div class="stat-value">{{ stats.contacts_added }}</div>
            <div class="stat-sub">added</div>
            <span class="stat-arrow">→</span>
          </a>
          <a class="stat-card" routerLink="/signal-briefs">
            <div class="stat-label">Briefs</div>
            <div class="stat-value">{{ stats.briefs_generated }}</div>
            <div class="stat-sub">generated</div>
            <span class="stat-arrow">→</span>
          </a>
          <a class="stat-card" routerLink="/outreach">
            <div class="stat-label">Outreach Drafts</div>
            <div class="stat-value">{{ stats.outreach_drafts }}</div>
            <div class="stat-sub">created</div>
            <span class="stat-arrow">→</span>
          </a>
          <a class="stat-card highlight" routerLink="/pipeline">
            <div class="stat-label">Calls Booked</div>
            <div class="stat-value accent">{{ stats.calls_booked }}</div>
            <div class="stat-sub">pipeline stage 6</div>
            <span class="stat-arrow">→</span>
          </a>
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
            <a routerLink="/sprint" class="action-card">
              <span class="material-icons">rocket_launch</span>
              <span>Sprint Board</span>
            </a>
            <a routerLink="/outreach" class="action-card">
              <span class="material-icons">send</span>
              <span>Draft Outreach</span>
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
  isFriday = new Date().getDay() === 5;

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
