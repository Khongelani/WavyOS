import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ExecutionService, WeeklySnapshot } from '../../../core/services/execution.service';

interface ScoreboardMetric {
  key: keyof WeeklySnapshot;
  label: string;
  value: number;
  isPrimary: boolean;
  amberThreshold: number | null;
  redThreshold: number;
}

@Component({
  selector: 'app-execution-scoreboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="scoreboard" aria-label="Execution Scoreboard">
      <div class="scoreboard-header">
        <span class="scoreboard-title">This Week</span>
        @if (snapshot) {
          <span class="week-label mono">w/c {{ snapshot.week_start_date | date:'d MMM' }}</span>
        }
      </div>

      @if (loading) {
        <div class="scoreboard-loading">Loading execution data...</div>
      } @else if (snapshot) {
        <div class="metrics-strip">
          <!-- Primary metric: conversations started -->
          <div class="metric-tile primary" [class]="colorClass(snapshot.messages_sent, 5, 0)">
            <div class="metric-value">{{ snapshot.messages_sent }}</div>
            <div class="metric-label">Conversations started</div>
          </div>

          <!-- Secondary metrics -->
          @for (m of secondaryMetrics; track m.key) {
            <div class="metric-tile" [class]="m.amberThreshold !== null ? colorClass(m.value, m.amberThreshold, m.redThreshold) : 'color-info'">
              <div class="metric-value secondary-val">{{ m.value }}</div>
              <div class="metric-label">{{ m.label }}</div>
            </div>
          }
        </div>
      }
    </div>
  `,
  styleUrl: './execution-scoreboard.component.scss',
})
export class ExecutionScoreboardComponent implements OnInit {
  snapshot: WeeklySnapshot | null = null;
  loading = true;

  secondaryMetrics: ScoreboardMetric[] = [];

  constructor(private execution: ExecutionService) {}

  ngOnInit(): void {
    this.execution.getCurrentSnapshot().subscribe({
      next: (s) => {
        this.snapshot = s;
        this.buildMetrics(s);
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }

  buildMetrics(s: WeeklySnapshot): void {
    this.secondaryMetrics = [
      { key: 'followups_sent', label: 'Follow-ups sent', value: s.followups_sent, isPrimary: false, amberThreshold: 3, redThreshold: 0 },
      { key: 'briefs_sent', label: 'Briefs sent', value: s.briefs_sent, isPrimary: false, amberThreshold: 1, redThreshold: 0 },
      { key: 'calls_requested', label: 'Calls requested', value: s.calls_requested, isPrimary: false, amberThreshold: 1, redThreshold: 0 },
      { key: 'replies_received', label: 'Replies received', value: s.replies_received, isPrimary: false, amberThreshold: null, redThreshold: 0 },
      { key: 'companies_researched', label: 'Researched', value: s.companies_researched, isPrimary: false, amberThreshold: null, redThreshold: 0 },
    ];
  }

  colorClass(value: number, amberThreshold: number, redThreshold: number): string {
    if (value <= redThreshold) return 'color-red';
    if (amberThreshold !== null && value < amberThreshold) return 'color-amber';
    return 'color-green';
  }
}
