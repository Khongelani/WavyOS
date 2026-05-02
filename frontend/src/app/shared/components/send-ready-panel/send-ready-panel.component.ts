import { Component, Input, Output, EventEmitter, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { OutreachDraft } from '../../../core/services/api.service';
import { ExecutionService } from '../../../core/services/execution.service';

interface CopyState {
  key: string;
  copied: boolean;
}

@Component({
  selector: 'app-send-ready-panel',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (draft) {
      <div class="send-ready-panel">
        <!-- Copy buttons per variant -->
        <div class="copy-grid">
          @if (draft.linkedin_message) {
            <div class="draft-block">
              <div class="draft-meta">
                <span class="draft-variant-label">LinkedIn</span>
                <span class="char-count mono">{{ draft.linkedin_message.length }}/200</span>
              </div>
              <div class="draft-body">{{ draft.linkedin_message }}</div>
              <button class="copy-btn" (click)="copy('linkedin', draft.linkedin_message!)">
                {{ getCopyLabel('linkedin') }}
              </button>
            </div>
          }

          @if (draft.email_body) {
            <div class="draft-block">
              <div class="draft-meta">
                <span class="draft-variant-label">Email</span>
                @if (draft.email_subject) {
                  <span class="email-subject">{{ draft.email_subject }}</span>
                }
              </div>
              <pre class="draft-body email-pre">{{ draft.email_body }}</pre>
              <button class="copy-btn" (click)="copy('email', (draft.email_subject ? draft.email_subject + '\n\n' : '') + draft.email_body!)">
                {{ getCopyLabel('email') }}
              </button>
            </div>
          }

          @if (draft.followup_message) {
            <div class="draft-block">
              <div class="draft-meta">
                <span class="draft-variant-label">Follow-up</span>
              </div>
              <div class="draft-body">{{ draft.followup_message }}</div>
              <button class="copy-btn" (click)="copy('followup', draft.followup_message!)">
                {{ getCopyLabel('followup') }}
              </button>
            </div>
          }

          @if (draft.gatekeeper_version) {
            <div class="draft-block">
              <div class="draft-meta">
                <span class="draft-variant-label">Gatekeeper</span>
              </div>
              <div class="draft-body">{{ draft.gatekeeper_version }}</div>
              <button class="copy-btn" (click)="copy('gatekeeper', draft.gatekeeper_version!)">
                {{ getCopyLabel('gatekeeper') }}
              </button>
            </div>
          }

          @if (draft.technical_validator_version) {
            <div class="draft-block">
              <div class="draft-meta">
                <span class="draft-variant-label">Technical Validator</span>
              </div>
              <div class="draft-body">{{ draft.technical_validator_version }}</div>
              <button class="copy-btn" (click)="copy('tech', draft.technical_validator_version!)">
                {{ getCopyLabel('tech') }}
              </button>
            </div>
          }
        </div>

        <!-- Mark as sent -->
        <div class="mark-sent-section">
          <div class="send-status">
            @if (draft.status === 'sent') {
              <div class="sent-indicator">
                <span class="sent-dot"></span>
                <span>Sent {{ draft.marked_sent_at | date:'d MMM, HH:mm' }}</span>
                @if (draft.followup_due_at) {
                  <span class="followup-info">
                    · Follow-up due {{ draft.followup_due_at | date:'d MMM' }}
                  </span>
                }
              </div>
            } @else {
              @if (markSentConfirmation) {
                <div class="sent-confirmation">
                  {{ markSentConfirmation }}
                </div>
              } @else {
                <button class="btn-mark-sent" (click)="markSent()" [disabled]="marking">
                  {{ marking ? 'Recording...' : 'Mark as sent →' }}
                </button>
              }
              <div class="no-auto-send-note">
                No messages are sent automatically. This records your manual action.
              </div>
            }
          </div>
        </div>
      </div>
    }
  `,
  styleUrl: './send-ready-panel.component.scss',
})
export class SendReadyPanelComponent implements OnChanges {
  @Input() draft!: OutreachDraft;
  @Output() sent = new EventEmitter<void>();

  copyStates: Map<string, boolean> = new Map();
  marking = false;
  markSentConfirmation = '';

  constructor(private execution: ExecutionService) {}

  ngOnChanges(): void {
    this.markSentConfirmation = '';
  }

  getCopyLabel(key: string): string {
    return this.copyStates.get(key) ? 'Copied!' : 'Copy';
  }

  copy(key: string, text: string): void {
    navigator.clipboard.writeText(text).then(() => {
      this.copyStates.set(key, true);
      setTimeout(() => {
        this.copyStates.set(key, false);
      }, 1500);
    });
  }

  markSent(): void {
    if (!this.draft || this.marking) return;
    this.marking = true;
    this.execution.markDraftSent(this.draft.id).subscribe({
      next: (result) => {
        this.marking = false;
        const dueDate = result.followup_due_at
          ? new Date(result.followup_due_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
          : '';
        this.markSentConfirmation = `Sent. Follow-up task created${dueDate ? ' for ' + dueDate : ''}.`;
        // Update draft status in place
        this.draft = { ...this.draft, status: 'sent', marked_sent_at: result.marked_sent_at, followup_due_at: result.followup_due_at };
        this.sent.emit();
      },
      error: () => {
        this.marking = false;
      },
    });
  }
}
