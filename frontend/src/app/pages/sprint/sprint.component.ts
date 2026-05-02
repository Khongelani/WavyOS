import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ExecutionService, SprintSummary, SprintCompany } from '../../core/services/execution.service';
import { ApiService, PipelineStage } from '../../core/services/api.service';

@Component({
  selector: 'app-sprint',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Weekly Sprint Board</h2>
          <span class="subtitle">Execute — not plan</span>
        </div>
      </div>

      @if (loading) {
        <div class="loading">Loading sprint data...</div>
      } @else if (summary) {
        <!-- Summary strip -->
        <div class="summary-strip">
          <div class="summary-stat">
            <span class="summary-val">{{ summary.active_companies }}</span>
            <span class="summary-label">active companies</span>
          </div>
          <div class="summary-sep">·</div>
          <div class="summary-stat" [class.has-action]="summary.need_action > 0">
            <span class="summary-val" [class.amber]="summary.need_action > 0">{{ summary.need_action }}</span>
            <span class="summary-label">need action</span>
          </div>
          <div class="summary-sep">·</div>
          <div class="summary-stat">
            <span class="summary-val green">{{ summary.moved_forward_this_week }}</span>
            <span class="summary-label">moved forward this week</span>
          </div>
        </div>

        <!-- Company list -->
        @if (summary.companies.length === 0) {
          <div class="empty-state">
            <span class="material-icons">rocket_launch</span>
            <p>No active companies in the pipeline yet.</p>
          </div>
        } @else {
          <div class="sprint-list">
            <!-- Group by stage -->
            @for (group of groupedByStage; track group.stageName) {
              <div class="stage-group">
                <div class="stage-group-header">
                  <span class="stage-dot" [style.background]="group.stageColor"></span>
                  <span class="stage-group-name">{{ group.stageName }}</span>
                  <span class="stage-group-count mono">{{ group.companies.length }}</span>
                </div>

                @for (company of group.companies; track company.id) {
                  <div class="sprint-row" [class.needs-action]="company.needs_action">
                    <div class="sprint-row-main">
                      <div class="company-info">
                        <a [routerLink]="['/companies', company.id]" class="company-name">
                          {{ company.name }}
                        </a>
                        @if (company.industry) {
                          <span class="industry-tag">{{ company.industry }}</span>
                        }
                      </div>

                      <div class="sprint-meta">
                        <span class="days-badge" [class.amber]="company.needs_action">
                          {{ company.days_in_stage }}d in stage
                        </span>
                        @if (company.last_task_due) {
                          <span class="task-due mono muted">
                            task: {{ company.last_task_due | date:'d MMM' }}
                          </span>
                        }
                      </div>
                    </div>

                    <div class="sprint-actions">
                      <select class="stage-select-mini"
                              [(ngModel)]="company.pipeline_stage_id"
                              (ngModelChange)="moveCompany(company, $event)">
                        @for (s of stages; track s.id) {
                          <option [value]="s.id">{{ s.name }}</option>
                        }
                      </select>
                      <button class="action-btn forward-btn" (click)="moveForward(company)" title="Move forward one stage">
                        <span class="material-icons">arrow_forward</span>
                      </button>
                      <button class="action-btn dismiss-btn" (click)="markLost(company)" title="Mark not relevant">
                        <span class="material-icons">close</span>
                      </button>
                    </div>
                  </div>
                }
              </div>
            }
          </div>
        }
      }
    </div>
  `,
  styleUrl: './sprint.component.scss',
})
export class SprintComponent implements OnInit {
  summary: SprintSummary | null = null;
  stages: PipelineStage[] = [];
  loading = true;

  get groupedByStage(): { stageName: string; stageColor: string; companies: SprintCompany[] }[] {
    if (!this.summary) return [];
    const map = new Map<string, { stageName: string; stageColor: string; companies: SprintCompany[] }>();
    for (const c of this.summary.companies) {
      const key = c.pipeline_stage_name || 'Unassigned';
      const color = c.pipeline_stage_color || '#64748B';
      if (!map.has(key)) {
        map.set(key, { stageName: key, stageColor: color, companies: [] });
      }
      map.get(key)!.companies.push(c);
    }
    return Array.from(map.values());
  }

  constructor(private execution: ExecutionService, private api: ApiService) {}

  ngOnInit(): void {
    this.api.getPipelineStages().subscribe(s => (this.stages = s));
    this.load();
  }

  load(): void {
    this.loading = true;
    this.execution.getSprintCompanies().subscribe({
      next: (s) => { this.summary = s; this.loading = false; },
      error: () => (this.loading = false),
    });
  }

  moveCompany(company: SprintCompany, stageId: number): void {
    this.api.updateCompany(company.id, { pipeline_stage_id: +stageId }).subscribe(() => this.load());
  }

  moveForward(company: SprintCompany): void {
    const currentIdx = this.stages.findIndex(s => s.id === company.pipeline_stage_id);
    if (currentIdx < this.stages.length - 1) {
      const nextStage = this.stages[currentIdx + 1];
      this.api.updateCompany(company.id, { pipeline_stage_id: nextStage.id }).subscribe(() => this.load());
    }
  }

  markLost(company: SprintCompany): void {
    const lostStage = this.stages.find(s => s.name === 'Lost');
    if (lostStage) {
      this.api.updateCompany(company.id, { pipeline_stage_id: lostStage.id }).subscribe(() => this.load());
    } else {
      this.api.updateCompany(company.id, { status: 'lost' }).subscribe(() => this.load());
    }
  }
}
