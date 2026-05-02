import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ExecutionService, Alert } from '../../../core/services/execution.service';

@Component({
  selector: 'app-anti-loop-alerts',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (visibleAlerts.length > 0) {
      <div class="alerts-strip">
        @for (alert of visibleAlerts; track alert.id) {
          <div class="alert-row">
            <span class="alert-icon">▲</span>
            <span class="alert-text">{{ alert.text }}</span>
            <button class="dismiss-btn" (click)="dismiss(alert.id)" title="Dismiss">×</button>
          </div>
        }
      </div>
    }
  `,
  styleUrl: './anti-loop-alerts.component.scss',
})
export class AntiLoopAlertsComponent implements OnInit {
  alerts: Alert[] = [];
  dismissedKeys = new Set<string>();

  get visibleAlerts(): Alert[] {
    return this.alerts.filter(a => !this.dismissedKeys.has(this.storageKey(a.id)));
  }

  constructor(private execution: ExecutionService) {}

  ngOnInit(): void {
    this.loadDismissed();
    this.execution.getAlerts().subscribe({
      next: (a) => (this.alerts = a),
    });
  }

  private weekKey(): string {
    const today = new Date();
    const monday = new Date(today);
    monday.setDate(today.getDate() - today.getDay() + 1);
    return monday.toISOString().slice(0, 10);
  }

  private storageKey(alertId: string): string {
    return `wavy_alert_dismissed_${alertId}_${this.weekKey()}`;
  }

  private loadDismissed(): void {
    const week = this.weekKey();
    for (const key of Object.keys(localStorage)) {
      if (key.startsWith('wavy_alert_dismissed_') && key.endsWith(week)) {
        this.dismissedKeys.add(key);
      }
    }
  }

  dismiss(alertId: string): void {
    const key = this.storageKey(alertId);
    localStorage.setItem(key, '1');
    this.dismissedKeys.add(key);
  }
}
