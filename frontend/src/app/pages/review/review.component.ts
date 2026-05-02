import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ExecutionService, WeeklyReview, WeeklySnapshot } from '../../core/services/execution.service';

@Component({
  selector: 'app-review',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Weekly Review</h2>
          @if (snapshot) {
            <span class="subtitle">Week of {{ snapshot.week_start_date | date:'d MMM yyyy' }}</span>
          }
        </div>
      </div>

      @if (loading) {
        <div class="loading">Loading review...</div>
      } @else {
        <!-- Section 1: This week's metrics (from snapshot) -->
        @if (snapshot) {
          <div class="card metrics-summary">
            <div class="metrics-row">
              <div class="metric-item">
                <span class="m-val">{{ snapshot.messages_sent }}</span>
                <span class="m-label">Messages sent</span>
              </div>
              <div class="metric-item">
                <span class="m-val">{{ snapshot.replies_received }}</span>
                <span class="m-label">Replies received</span>
              </div>
              <div class="metric-item">
                <span class="m-val">{{ snapshot.companies_researched }}</span>
                <span class="m-label">Companies researched</span>
              </div>
              <div class="metric-item">
                <span class="m-val">{{ snapshot.followups_sent }}</span>
                <span class="m-label">Follow-ups sent</span>
              </div>
            </div>
          </div>
        }

        <!-- Section 2: Reflection inputs -->
        <div class="card reflection-card">
          <h3>Reflection</h3>

          <div class="review-field">
            <label>What was sent this week?</label>
            <textarea [(ngModel)]="review.what_was_sent" rows="3"
                      placeholder="Summarise what you sent and to whom..."></textarea>
          </div>

          <div class="review-field">
            <label>Who replied?</label>
            <textarea [(ngModel)]="review.who_replied" rows="2"
                      placeholder="Names, companies, or types of response..."></textarea>
          </div>

          <div class="review-field">
            <label>What message worked?</label>
            <textarea [(ngModel)]="review.what_worked" rows="2"
                      placeholder="Which angle, phrasing or hook got a response..."></textarea>
          </div>

          <div class="review-field">
            <label>What industry responded?</label>
            <textarea [(ngModel)]="review.industry_response" rows="2"
                      placeholder="Mining, logistics, insurance... pattern?"></textarea>
          </div>

          <div class="review-field">
            <label>What will change next week?</label>
            <textarea [(ngModel)]="review.change_next_week" rows="2"
                      placeholder="One concrete change to how you operate..."></textarea>
          </div>

          <div class="reflection-actions">
            <button class="btn-primary" (click)="saveReview()" [disabled]="saving">
              {{ saving ? 'Saving...' : 'Save Reflection' }}
            </button>
            @if (savedMsg) {
              <span class="saved-msg">{{ savedMsg }}</span>
            }
          </div>
        </div>

        <!-- Section 3: AI-generated plan -->
        <div class="card ai-plan-card">
          <div class="ai-plan-header">
            <h3>Next Week Plan</h3>
            @if (!hasGenerated) {
              <button class="btn-primary" (click)="generatePlan()" [disabled]="generating">
                {{ generating ? 'Generating...' : 'Generate next week plan' }}
              </button>
            } @else {
              <button class="btn-ghost btn-sm" (click)="generatePlan()" [disabled]="generating">
                Regenerate
              </button>
            }
          </div>

          @if (review.is_demo_plan) {
            <div class="demo-badge">DEMO OUTPUT</div>
          }

          @if (hasGenerated) {
            @if (review.generated_targets?.length) {
              <div class="plan-section">
                <div class="plan-label">Priority Targets Next Week</div>
                <ul>
                  @for (t of review.generated_targets; track t) {
                    <li>{{ t }}</li>
                  }
                </ul>
              </div>
            }

            @if (review.generated_angle) {
              <div class="plan-section">
                <div class="plan-label">Improved Angle</div>
                <p>{{ review.generated_angle }}</p>
              </div>
            }

            @if (review.top_followups?.length) {
              <div class="plan-section">
                <div class="plan-label">Top Follow-ups</div>
                @for (f of review.top_followups; track f.contact) {
                  <div class="followup-card">
                    <div class="followup-who">
                      <strong>{{ f.contact }}</strong>
                      <span class="muted"> at {{ f.company }}</span>
                    </div>
                    <div class="followup-reason">{{ f.reason }}</div>
                  </div>
                }
              </div>
            }
          } @else if (!generating) {
            <div class="plan-empty">
              Fill in at least "What worked" and "What industry responded", then generate your plan.
            </div>
          }

          @if (generating) {
            <div class="loading">Generating plan...</div>
          }
        </div>
      }
    </div>
  `,
  styleUrl: './review.component.scss',
})
export class ReviewComponent implements OnInit {
  snapshot: WeeklySnapshot | null = null;
  review: WeeklyReview & { is_demo_plan?: boolean } = {} as WeeklyReview;
  loading = true;
  saving = false;
  generating = false;
  savedMsg = '';

  get hasGenerated(): boolean {
    return !!(this.review.generated_angle || this.review.generated_targets?.length);
  }

  constructor(private execution: ExecutionService) {}

  ngOnInit(): void {
    this.execution.getCurrentSnapshot().subscribe(s => (this.snapshot = s));
    this.execution.getCurrentReview().subscribe({
      next: (r) => {
        this.review = r;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }

  saveReview(): void {
    this.saving = true;
    this.execution.updateReview({
      what_was_sent: this.review.what_was_sent,
      who_replied: this.review.who_replied,
      what_worked: this.review.what_worked,
      industry_response: this.review.industry_response,
      change_next_week: this.review.change_next_week,
    }).subscribe({
      next: (r) => {
        this.review = { ...this.review, ...r };
        this.saving = false;
        this.savedMsg = 'Saved.';
        setTimeout(() => (this.savedMsg = ''), 3000);
      },
      error: () => (this.saving = false),
    });
  }

  generatePlan(): void {
    this.generating = true;
    this.execution.generateReview(
      this.review.what_worked || '',
      this.review.industry_response || '',
    ).subscribe({
      next: (r) => {
        this.review = { ...this.review, ...r };
        this.generating = false;
      },
      error: () => (this.generating = false),
    });
  }
}
