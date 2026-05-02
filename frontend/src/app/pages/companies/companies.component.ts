import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService, Company, PipelineStage } from '../../core/services/api.service';

@Component({
  selector: 'app-companies',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, ReactiveFormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Companies</h2>
          <span class="subtitle">{{ companies.length }} total</span>
        </div>
        <button class="btn-primary" (click)="showForm = !showForm">
          <span class="material-icons">add</span> Add Company
        </button>
      </div>

      <!-- Add form -->
      @if (showForm) {
        <div class="card form-card">
          <h3>New Company</h3>
          <form [formGroup]="form" (ngSubmit)="create()">
            <div class="form-grid">
              <div class="field">
                <label>Company Name *</label>
                <input formControlName="name" placeholder="e.g. Kumba Iron Ore">
              </div>
              <div class="field">
                <label>Industry</label>
                <input formControlName="industry" placeholder="e.g. Mining">
              </div>
              <div class="field">
                <label>Website</label>
                <input formControlName="website" placeholder="https://...">
              </div>
              <div class="field">
                <label>Country</label>
                <input formControlName="country" placeholder="e.g. South Africa">
              </div>
              <div class="field">
                <label>Pipeline Stage</label>
                <select formControlName="pipeline_stage_id">
                  <option [value]="null">— None —</option>
                  @for (s of stages; track s.id) {
                    <option [value]="s.id">{{ s.name }}</option>
                  }
                </select>
              </div>
            </div>
            <div class="field full">
              <label>Notes</label>
              <textarea formControlName="notes" rows="3" placeholder="Internal notes..."></textarea>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-ghost" (click)="showForm = false">Cancel</button>
              <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">
                {{ saving ? 'Saving...' : 'Add Company' }}
              </button>
            </div>
          </form>
        </div>
      }

      <!-- Search & filter -->
      <div class="toolbar">
        <div class="search-box">
          <span class="material-icons">search</span>
          <input [(ngModel)]="searchQuery" (ngModelChange)="onSearch()" placeholder="Search companies...">
        </div>
        <select [(ngModel)]="stageFilter" (ngModelChange)="onSearch()" class="stage-filter">
          <option [value]="null">All stages</option>
          @for (s of stages; track s.id) {
            <option [value]="s.id">{{ s.name }}</option>
          }
        </select>
      </div>

      <!-- Table -->
      @if (loading) {
        <div class="loading">Loading companies...</div>
      } @else if (companies.length === 0) {
        <div class="empty-state">
          <span class="material-icons">business</span>
          <p>No companies yet. Add your first target.</p>
        </div>
      } @else {
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Industry</th>
                <th>Country</th>
                <th>Stage</th>
                <th>Research</th>
                <th>Contacts</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              @for (c of companies; track c.id) {
                <tr>
                  <td class="company-name">
                    <a [routerLink]="['/companies', c.id]">{{ c.name }}</a>
                  </td>
                  <td class="muted">{{ c.industry || '—' }}</td>
                  <td class="muted">{{ c.country || '—' }}</td>
                  <td>
                    @if (c.pipeline_stage) {
                      <span class="stage-badge" [style.border-color]="c.pipeline_stage.color"
                            [style.color]="c.pipeline_stage.color">
                        {{ c.pipeline_stage.name }}
                      </span>
                    } @else {
                      <span class="muted">—</span>
                    }
                  </td>
                  <td class="mono">{{ c.research_count || 0 }}</td>
                  <td class="mono">{{ c.contact_count || 0 }}</td>
                  <td>
                    <a [routerLink]="['/companies', c.id]" class="link-btn">View →</a>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
  styleUrl: './companies.component.scss',
})
export class CompaniesComponent implements OnInit {
  companies: Company[] = [];
  stages: PipelineStage[] = [];
  loading = true;
  showForm = false;
  saving = false;
  searchQuery = '';
  stageFilter: number | null = null;
  form: FormGroup;

  constructor(private api: ApiService, private fb: FormBuilder) {
    this.form = this.fb.group({
      name: ['', Validators.required],
      industry: [''],
      website: [''],
      country: [''],
      notes: [''],
      pipeline_stage_id: [null],
    });
  }

  ngOnInit(): void {
    this.load();
    this.api.getPipelineStages().subscribe(s => (this.stages = s));
  }

  load(): void {
    this.loading = true;
    this.api.getCompanies(this.searchQuery || undefined, this.stageFilter || undefined).subscribe({
      next: (cs) => {
        this.companies = cs;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }

  onSearch(): void {
    this.load();
  }

  create(): void {
    if (this.form.invalid) return;
    this.saving = true;
    const val = this.form.value;
    if (val.pipeline_stage_id === 'null' || val.pipeline_stage_id === null) {
      val.pipeline_stage_id = null;
    } else {
      val.pipeline_stage_id = +val.pipeline_stage_id;
    }
    this.api.createCompany(val).subscribe({
      next: () => {
        this.showForm = false;
        this.form.reset();
        this.saving = false;
        this.load();
      },
      error: () => (this.saving = false),
    });
  }
}
