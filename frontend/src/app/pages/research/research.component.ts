import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService, Company, ResearchReport } from '../../core/services/api.service';

@Component({
  selector: 'app-research',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Research Agent</h2>
          <span class="subtitle">Generate company intelligence reports</span>
        </div>
      </div>

      <div class="card research-launcher">
        <h3>Run Company Research</h3>
        <div class="form-grid">
          <div class="field">
            <label>Company *</label>
            <select [(ngModel)]="selectedCompanyId" (ngModelChange)="onCompanySelect()">
              <option [value]="null">— Select company —</option>
              @for (c of companies; track c.id) {
                <option [value]="c.id">{{ c.name }}</option>
              }
            </select>
          </div>
          <div class="field">
            <label>Override Company Name</label>
            <input [(ngModel)]="overrideName" placeholder="Leave blank to use stored name">
          </div>
          <div class="field">
            <label>Website</label>
            <input [(ngModel)]="overrideWebsite" placeholder="https://...">
          </div>
          <div class="field">
            <label>Industry</label>
            <input [(ngModel)]="overrideIndustry" placeholder="e.g. Mining">
          </div>
        </div>
        <div class="launch-footer">
          <p class="hint">
            @if (!hasApiKey) {
              <span class="demo-note">⚠ No OpenAI key configured — will return demo output</span>
            }
          </p>
          <button class="btn-primary" (click)="runResearch()" [disabled]="!selectedCompanyId || running">
            {{ running ? 'Running research...' : 'Run Research' }}
          </button>
        </div>
      </div>

      @if (result) {
        <div class="card result-card">
          @if (result.is_demo) {
            <div class="demo-badge">DEMO OUTPUT — No OpenAI key configured</div>
          }
          <div class="confidence-bar">
            <span class="mono muted">Confidence</span>
            <div class="bar">
              <div class="bar-fill" [style.width.%]="(result.confidence_score || 0) * 100"></div>
            </div>
            <span class="mono">{{ (result.confidence_score || 0) | percent:'1.0-0' }}</span>
          </div>

          <div class="result-section">
            <div class="result-label">Overview</div>
            <p>{{ result.overview }}</p>
          </div>

          @if (result.signals?.length) {
            <div class="result-section">
              <div class="result-label">Recent Signals</div>
              <ul>@for (s of result.signals; track s) { <li>{{ s }}</li> }</ul>
            </div>
          }

          @if (result.cashflow_pressures?.length) {
            <div class="result-section">
              <div class="result-label">Cashflow Pressure Points</div>
              <ul>@for (s of result.cashflow_pressures; track s) { <li>{{ s }}</li> }</ul>
            </div>
          }

          @if (result.buyer_personas?.length) {
            <div class="result-section">
              <div class="result-label">Buyer Personas</div>
              <div class="persona-grid">
                @for (p of result.buyer_personas; track p.title) {
                  <div class="persona-card">
                    <strong>{{ p.title }}</strong>
                    <p>{{ p.why }}</p>
                  </div>
                }
              </div>
            </div>
          }

          @if (result.outreach_angle) {
            <div class="result-section">
              <div class="result-label">Outreach Angle</div>
              <p>{{ result.outreach_angle }}</p>
            </div>
          }

          <div class="result-actions">
            <a [routerLink]="['/companies', selectedCompanyId]" class="btn-primary btn-sm">
              View Company →
            </a>
          </div>
        </div>
      }
    </div>
  `,
  styleUrl: './research.component.scss',
})
export class ResearchComponent implements OnInit {
  companies: Company[] = [];
  selectedCompanyId: number | null = null;
  overrideName = '';
  overrideWebsite = '';
  overrideIndustry = '';
  running = false;
  result: ResearchReport | null = null;
  hasApiKey = false;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getCompanies().subscribe(c => (this.companies = c));
    this.api.getHealth().subscribe(h => (this.hasApiKey = h.ai !== 'demo_mode'));
  }

  onCompanySelect(): void {
    const c = this.companies.find(x => x.id === +this.selectedCompanyId!);
    if (c) {
      this.overrideWebsite = c.website || '';
      this.overrideIndustry = c.industry || '';
    }
  }

  runResearch(): void {
    if (!this.selectedCompanyId) return;
    this.running = true;
    this.result = null;
    const payload: Record<string, string> = {};
    if (this.overrideName) payload['company_name'] = this.overrideName;
    if (this.overrideWebsite) payload['website'] = this.overrideWebsite;
    if (this.overrideIndustry) payload['industry'] = this.overrideIndustry;

    this.api.runResearch(this.selectedCompanyId, payload).subscribe({
      next: (r) => {
        this.result = r;
        this.running = false;
      },
      error: () => (this.running = false),
    });
  }
}
