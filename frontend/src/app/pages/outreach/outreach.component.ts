import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, Company, Contact, SignalBrief, OutreachDraft } from '../../core/services/api.service';

@Component({
  selector: 'app-outreach',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Outreach Agent</h2>
          <span class="subtitle">Draft outreach messages — review before sending</span>
        </div>
      </div>

      <div class="warning-banner">
        <span class="material-icons">warning</span>
        <strong>Review before sending.</strong> No messages are sent automatically. All output is draft text only — copy manually.
      </div>

      <div class="card generator">
        <h3>Generate Outreach Draft</h3>
        <div class="form-grid">
          <div class="field">
            <label>Company *</label>
            <select [(ngModel)]="selectedCompanyId" (ngModelChange)="onCompanyChange()">
              <option [value]="null">— Select company —</option>
              @for (c of companies; track c.id) {
                <option [value]="c.id">{{ c.name }}</option>
              }
            </select>
          </div>
          <div class="field">
            <label>Contact *</label>
            <select [(ngModel)]="selectedContactId" [disabled]="!selectedCompanyId">
              <option [value]="null">— Select contact —</option>
              @for (c of contacts; track c.id) {
                <option [value]="c.id">{{ c.name }} ({{ c.role }})</option>
              }
            </select>
          </div>
          <div class="field">
            <label>Signal Brief (optional)</label>
            <select [(ngModel)]="selectedBriefId" [disabled]="!selectedCompanyId">
              <option [value]="null">— No brief —</option>
              @for (b of briefs; track b.id) {
                <option [value]="b.id">Brief #{{ b.id }}{{ b.is_demo ? ' (demo)' : '' }}</option>
              }
            </select>
          </div>
          <div class="field">
            <label>Tone</label>
            <select [(ngModel)]="tone">
              <option value="professional">Professional</option>
              <option value="direct">Direct</option>
              <option value="warm">Warm</option>
            </select>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn-primary" (click)="generate()"
                  [disabled]="!selectedCompanyId || !selectedContactId || generating">
            {{ generating ? 'Generating...' : 'Generate Drafts' }}
          </button>
        </div>
      </div>

      @if (draft) {
        <div class="drafts">
          @if (draft.is_demo) {
            <div class="demo-badge">DEMO OUTPUT</div>
          }

          <div class="draft-card">
            <div class="draft-label">LinkedIn Message
              <span class="char-count mono">{{ (draft.linkedin_message || '').length }}/200</span>
            </div>
            <div class="draft-content">{{ draft.linkedin_message }}</div>
            <button class="copy-btn" (click)="copy(draft.linkedin_message)">
              <span class="material-icons">content_copy</span> Copy
            </button>
          </div>

          <div class="draft-card">
            <div class="draft-label">Email Subject</div>
            <div class="draft-content subject">{{ draft.email_subject }}</div>
            <button class="copy-btn" (click)="copy(draft.email_subject)">
              <span class="material-icons">content_copy</span> Copy
            </button>
          </div>

          <div class="draft-card">
            <div class="draft-label">Email Body</div>
            <pre class="draft-content">{{ draft.email_body }}</pre>
            <button class="copy-btn" (click)="copy(draft.email_body)">
              <span class="material-icons">content_copy</span> Copy
            </button>
          </div>

          <div class="draft-card">
            <div class="draft-label">Follow-up Message</div>
            <div class="draft-content">{{ draft.followup_message }}</div>
            <button class="copy-btn" (click)="copy(draft.followup_message)">
              <span class="material-icons">content_copy</span> Copy
            </button>
          </div>

          <div class="draft-card">
            <div class="draft-label">Gatekeeper Version</div>
            <div class="draft-content">{{ draft.gatekeeper_version }}</div>
            <button class="copy-btn" (click)="copy(draft.gatekeeper_version)">
              <span class="material-icons">content_copy</span> Copy
            </button>
          </div>

          <div class="draft-card">
            <div class="draft-label">Technical Validator Version</div>
            <div class="draft-content">{{ draft.technical_validator_version }}</div>
            <button class="copy-btn" (click)="copy(draft.technical_validator_version)">
              <span class="material-icons">content_copy</span> Copy
            </button>
          </div>

          @if (copied) {
            <div class="copy-toast">Copied to clipboard!</div>
          }
        </div>
      }
    </div>
  `,
  styleUrl: './outreach.component.scss',
})
export class OutreachComponent implements OnInit {
  companies: Company[] = [];
  contacts: Contact[] = [];
  briefs: SignalBrief[] = [];
  selectedCompanyId: number | null = null;
  selectedContactId: number | null = null;
  selectedBriefId: number | null = null;
  tone = 'professional';
  generating = false;
  draft: OutreachDraft | null = null;
  copied = false;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getCompanies().subscribe(c => (this.companies = c));
  }

  onCompanyChange(): void {
    this.contacts = [];
    this.briefs = [];
    this.selectedContactId = null;
    this.selectedBriefId = null;
    if (!this.selectedCompanyId) return;
    this.api.getContacts(+this.selectedCompanyId).subscribe(c => (this.contacts = c));
    this.api.getBriefs(+this.selectedCompanyId).subscribe(b => (this.briefs = b));
  }

  generate(): void {
    if (!this.selectedCompanyId || !this.selectedContactId) return;
    this.generating = true;
    this.draft = null;
    this.api.generateOutreach({
      contact_id: +this.selectedContactId,
      company_id: +this.selectedCompanyId,
      brief_id: this.selectedBriefId ? +this.selectedBriefId : undefined,
      tone: this.tone,
    }).subscribe({
      next: (d) => { this.draft = d; this.generating = false; },
      error: () => (this.generating = false),
    });
  }

  copy(text?: string): void {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      this.copied = true;
      setTimeout(() => (this.copied = false), 2000);
    });
  }
}
