import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService, PipelineColumn, PipelineStage, Company } from '../../core/services/api.service';

@Component({
  selector: 'app-pipeline',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Pipeline</h2>
          <span class="subtitle">{{ totalCompanies }} companies tracked</span>
        </div>
        <div class="view-toggle">
          <button [class.active]="view === 'board'" (click)="view = 'board'">
            <span class="material-icons">view_kanban</span>
          </button>
          <button [class.active]="view === 'list'" (click)="view = 'list'">
            <span class="material-icons">view_list</span>
          </button>
        </div>
      </div>

      @if (loading) {
        <div class="loading">Loading pipeline...</div>
      } @else if (view === 'board') {
        <div class="board">
          @for (col of columns; track col.stage.id) {
            <div class="board-col">
              <div class="col-header" [style.border-top-color]="col.stage.color">
                <span class="col-name">{{ col.stage.name }}</span>
                <span class="col-count mono">{{ col.companies.length }}</span>
              </div>
              @for (c of col.companies; track c.id) {
                <div class="pipeline-card">
                  <a [routerLink]="['/companies', c.id]" class="card-name">{{ c.name }}</a>
                  @if (c.industry) { <div class="card-sub">{{ c.industry }}</div> }
                  @if (c.updated_at) {
                    <div class="card-date mono">{{ formatDate(c.updated_at) }}</div>
                  }
                  <div class="card-move">
                    <select [(ngModel)]="c.pipeline_stage_id" (ngModelChange)="moveCompany(c, $event)" class="stage-mini-select">
                      @for (s of stages; track s.id) {
                        <option [value]="s.id">{{ s.name }}</option>
                      }
                    </select>
                  </div>
                </div>
              }
              @if (col.companies.length === 0) {
                <div class="empty-col">No companies</div>
              }
            </div>
          }
        </div>
      } @else {
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Industry</th>
                <th>Stage</th>
                <th>Last Updated</th>
                <th>Move To</th>
              </tr>
            </thead>
            <tbody>
              @for (col of columns; track col.stage.id) {
                @for (c of col.companies; track c.id) {
                  <tr>
                    <td>
                      <a [routerLink]="['/companies', c.id]" class="company-link">{{ c.name }}</a>
                    </td>
                    <td class="muted">{{ c.industry || '—' }}</td>
                    <td>
                      <span class="stage-badge" [style.border-color]="col.stage.color"
                            [style.color]="col.stage.color">
                        {{ col.stage.name }}
                      </span>
                    </td>
                    <td class="mono muted">{{ formatDate(c.updated_at) }}</td>
                    <td>
                      <select [(ngModel)]="c.pipeline_stage_id" (ngModelChange)="moveCompany(c, $event)" class="stage-mini-select">
                        @for (s of stages; track s.id) {
                          <option [value]="s.id">{{ s.name }}</option>
                        }
                      </select>
                    </td>
                  </tr>
                }
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
  styleUrl: './pipeline.component.scss',
})
export class PipelineComponent implements OnInit {
  columns: PipelineColumn[] = [];
  stages: PipelineStage[] = [];
  loading = true;
  view: 'board' | 'list' = 'board';

  get totalCompanies(): number {
    return this.columns.reduce((sum, c) => sum + c.companies.length, 0);
  }

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getPipelineStages().subscribe(s => (this.stages = s));
    this.load();
  }

  load(): void {
    this.api.getPipeline().subscribe({
      next: (cols) => { this.columns = cols; this.loading = false; },
      error: () => (this.loading = false),
    });
  }

  moveCompany(company: Partial<Company>, stageId: number): void {
    if (!company.id) return;
    this.api.updateCompany(company.id, { pipeline_stage_id: +stageId }).subscribe(() => this.load());
  }

  formatDate(dateStr?: string): string {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
  }
}
