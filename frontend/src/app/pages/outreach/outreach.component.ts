import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, Company, Contact, SignalBrief, OutreachDraft } from '../../core/services/api.service';
import { SendReadyPanelComponent } from '../../shared/components/send-ready-panel/send-ready-panel.component';

@Component({
  selector: 'app-outreach',
  standalone: true,
  imports: [CommonModule, FormsModule, SendReadyPanelComponent],
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
        <strong>Review before sending.</strong> No messages are sent automatically. All output is draft text only.
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
        <div class="draft-output">
          @if (draft.is_demo) {
            <div class="demo-badge">DEMO OUTPUT</div>
          }
          <!-- SendReadyPanel handles all copy + mark-as-sent flow -->
          <app-send-ready-panel [draft]="draft" (sent)="onDraftSent()" />
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

  onDraftSent(): void {
    // Draft was marked sent — refresh so the panel reflects the new state
    if (!this.draft) return;
    this.api.getCompanies().subscribe(); // trigger any refresh needed
  }
}
