import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService, Company, ResearchReport, SignalBrief } from '../../core/services/api.service';

@Component({
  selector: 'app-signal-briefs',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Signal Briefs</h2>
          <span class="subtitle">CFO-grade intelligence summaries</span>
        </div>
      </div>

      <div class="card generator">
        <h3>Generate Signal Brief</h3>
        <div class="form-row">
          <div class="field">
            <label>Company</label>
            <select [(ngModel)]="selectedCompanyId" (ngModelChange)="loadResearch()">
              <option [value]="null">— Select company —</option>
              @for (c of companies; track c.id) {
                <option [value]="c.id">{{ c.name }}</option>
              }
            </select>
          </div>
          <div class="field">
            <label>Research Report</label>
            <select [(ngModel)]="selectedResearchId" [disabled]="!selectedCompanyId || research.length === 0">
              <option [value]="null">— Select report —</option>
              @for (r of research; track r.id) {
                <option [value]="r.id">{{ r.created_at | date:'d MMM yyyy HH:mm' }}{{ r.is_demo ? ' (demo)' : '' }}</option>
              }
            </select>
          </div>
          <button class="btn-primary" (click)="generate()" [disabled]="!selectedCompanyId || !selectedResearchId || generating">
            {{ generating ? 'Generating...' : 'Generate Brief' }}
          </button>
        </div>
      </div>

      @if (newBrief) {
        <div class="card brief-result">
          @if (newBrief.is_demo) { <div class="demo-badge">DEMO OUTPUT</div> }
          <div class="brief-edit-mode">
            <div class="brief-edit-header">
              <span>Brief #{{ newBrief.id }}</span>
              <button class="btn-sm btn-ghost" (click)="editMode = !editMode">
                {{ editMode ? 'Preview' : 'Edit' }}
              </button>
            </div>

            @if (!editMode) {
              <div class="brief-view">
                <div class="bf">
                  <div class="bf-label">Executive Signal</div>
                  <p>{{ newBrief.executive_signal }}</p>
                </div>
                <div class="bf">
                  <div class="bf-label">Why It Matters</div>
                  <p>{{ newBrief.why_it_matters }}</p>
                </div>
                @if (newBrief.receivables_blind_spots?.length) {
                  <div class="bf">
                    <div class="bf-label">Receivables Blind Spots</div>
                    <ul>@for (s of newBrief.receivables_blind_spots; track s) { <li>{{ s }}</li> }</ul>
                  </div>
                }
                <div class="bf">
                  <div class="bf-label">Operational Impact</div>
                  <p>{{ newBrief.operational_impact }}</p>
                </div>
                <div class="bf">
                  <div class="bf-label">Suggested Action</div>
                  <p>{{ newBrief.suggested_action }}</p>
                </div>
                <div class="bf">
                  <div class="bf-label">Conversation Opener</div>
                  <blockquote>{{ newBrief.conversation_opener }}</blockquote>
                </div>
              </div>
            } @else {
              <div class="brief-edit">
                <div class="field">
                  <label>Executive Signal</label>
                  <textarea [(ngModel)]="editDraft.executive_signal" rows="3"></textarea>
                </div>
                <div class="field">
                  <label>Why It Matters</label>
                  <textarea [(ngModel)]="editDraft.why_it_matters" rows="3"></textarea>
                </div>
                <div class="field">
                  <label>Operational Impact</label>
                  <textarea [(ngModel)]="editDraft.operational_impact" rows="2"></textarea>
                </div>
                <div class="field">
                  <label>Suggested Action</label>
                  <textarea [(ngModel)]="editDraft.suggested_action" rows="2"></textarea>
                </div>
                <div class="field">
                  <label>Conversation Opener</label>
                  <textarea [(ngModel)]="editDraft.conversation_opener" rows="2"></textarea>
                </div>
                <div class="form-actions">
                  <button class="btn-primary" (click)="saveBrief()">Save Changes</button>
                </div>
              </div>
            }
          </div>
        </div>
      }
    </div>
  `,
  styleUrl: './signal-briefs.component.scss',
})
export class SignalBriefsComponent implements OnInit {
  companies: Company[] = [];
  research: ResearchReport[] = [];
  selectedCompanyId: number | null = null;
  selectedResearchId: number | null = null;
  generating = false;
  newBrief: SignalBrief | null = null;
  editMode = false;
  editDraft: Partial<SignalBrief> = {};

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getCompanies().subscribe(c => (this.companies = c));
  }

  loadResearch(): void {
    this.research = [];
    this.selectedResearchId = null;
    if (!this.selectedCompanyId) return;
    this.api.getResearch(+this.selectedCompanyId).subscribe(r => (this.research = r));
  }

  generate(): void {
    if (!this.selectedCompanyId || !this.selectedResearchId) return;
    this.generating = true;
    this.api.generateBrief(+this.selectedCompanyId, +this.selectedResearchId).subscribe({
      next: (b) => {
        this.newBrief = b;
        this.editDraft = { ...b };
        this.generating = false;
        this.editMode = false;
      },
      error: () => (this.generating = false),
    });
  }

  saveBrief(): void {
    if (!this.newBrief || !this.selectedCompanyId) return;
    this.api.updateBrief(+this.selectedCompanyId, this.newBrief.id, this.editDraft).subscribe(b => {
      this.newBrief = b;
      this.editMode = false;
    });
  }
}
