import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService, Company, ResearchReport, SignalBrief, Contact, Task, PipelineStage } from '../../core/services/api.service';

@Component({
  selector: 'app-company-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  template: `
    <div class="page">
      @if (loading) {
        <div class="loading">Loading...</div>
      } @else if (company) {
        <div class="page-header">
          <div>
            <a routerLink="/companies" class="back-link">← Companies</a>
            <h2>{{ company.name }}</h2>
            <div class="company-meta">
              @if (company.industry) { <span class="meta-tag">{{ company.industry }}</span> }
              @if (company.country) { <span class="meta-tag">{{ company.country }}</span> }
              @if (company.website) {
                <a [href]="company.website" target="_blank" class="meta-link">{{ company.website }}</a>
              }
            </div>
          </div>
          <div class="header-actions">
            <select [(ngModel)]="stageId" (ngModelChange)="updateStage()" class="stage-select">
              <option [value]="null">No stage</option>
              @for (s of stages; track s.id) {
                <option [value]="s.id">{{ s.name }}</option>
              }
            </select>
          </div>
        </div>

        <!-- Tabs -->
        <div class="tabs">
          @for (tab of tabs; track tab.key) {
            <button class="tab" [class.active]="activeTab === tab.key" (click)="activeTab = tab.key">
              {{ tab.label }}
              @if (counts[tab.key]) {
                <span class="tab-count">{{ counts[tab.key] }}</span>
              }
            </button>
          }
        </div>

        <!-- Research tab -->
        @if (activeTab === 'research') {
          <div class="tab-content">
            <div class="tab-header">
              <h3>Research Reports</h3>
              <button class="btn-primary btn-sm" (click)="runResearch()" [disabled]="researchRunning">
                {{ researchRunning ? 'Running...' : '+ Run Research' }}
              </button>
            </div>
            @for (r of research; track r.id) {
              <div class="card research-card">
                @if (r.is_demo) {
                  <div class="demo-badge">DEMO OUTPUT</div>
                }
                <div class="confidence">
                  Confidence: <span class="mono">{{ (r.confidence_score || 0) | percent:'1.0-0' }}</span>
                </div>
                <p class="overview-text">{{ r.overview }}</p>
                @if (r.signals?.length) {
                  <div class="signal-section">
                    <div class="signal-label">Recent Signals</div>
                    <ul>@for (s of r.signals; track s) { <li>{{ s }}</li> }</ul>
                  </div>
                }
                @if (r.cashflow_pressures?.length) {
                  <div class="signal-section">
                    <div class="signal-label">Cashflow Pressure Points</div>
                    <ul>@for (s of r.cashflow_pressures; track s) { <li>{{ s }}</li> }</ul>
                  </div>
                }
                @if (r.outreach_angle) {
                  <div class="signal-section">
                    <div class="signal-label">Outreach Angle</div>
                    <p>{{ r.outreach_angle }}</p>
                  </div>
                }
                <div class="card-footer">
                  <span class="mono muted">{{ r.created_at | date:'d MMM yyyy, HH:mm' }}</span>
                  <button class="btn-sm btn-accent" (click)="generateBrief(r.id)">Generate Brief →</button>
                </div>
              </div>
            }
            @if (research.length === 0) {
              <div class="empty-state">No research reports yet.</div>
            }
          </div>
        }

        <!-- Signal Briefs tab -->
        @if (activeTab === 'briefs') {
          <div class="tab-content">
            <h3>Signal Briefs</h3>
            @for (b of briefs; track b.id) {
              <div class="card brief-card">
                @if (b.is_demo) { <div class="demo-badge">DEMO OUTPUT</div> }
                @if (b.is_edited) { <div class="edited-badge">EDITED</div> }
                <div class="brief-field">
                  <div class="brief-label">Executive Signal</div>
                  <p>{{ b.executive_signal }}</p>
                </div>
                <div class="brief-field">
                  <div class="brief-label">Why It Matters</div>
                  <p>{{ b.why_it_matters }}</p>
                </div>
                <div class="brief-field">
                  <div class="brief-label">Conversation Opener</div>
                  <blockquote>{{ b.conversation_opener }}</blockquote>
                </div>
                <div class="card-footer">
                  <span class="mono muted">{{ b.created_at | date:'d MMM yyyy' }}</span>
                </div>
              </div>
            }
            @if (briefs.length === 0) {
              <div class="empty-state">No signal briefs yet. Run research first.</div>
            }
          </div>
        }

        <!-- Contacts tab -->
        @if (activeTab === 'contacts') {
          <div class="tab-content">
            <div class="tab-header">
              <h3>Contacts</h3>
              <button class="btn-primary btn-sm" (click)="showContactForm = !showContactForm">+ Add Contact</button>
            </div>
            @if (showContactForm) {
              <div class="inline-form card">
                <div class="form-grid">
                  <div class="field">
                    <label>Name *</label>
                    <input [(ngModel)]="newContact.name" placeholder="Full name">
                  </div>
                  <div class="field">
                    <label>Role</label>
                    <input [(ngModel)]="newContact.role" placeholder="CFO, Director...">
                  </div>
                  <div class="field">
                    <label>Email</label>
                    <input [(ngModel)]="newContact.email" placeholder="email@company.com">
                  </div>
                  <div class="field">
                    <label>LinkedIn URL</label>
                    <input [(ngModel)]="newContact.linkedin_url" placeholder="https://linkedin.com/in/...">
                  </div>
                  <div class="field">
                    <label>Contact Type</label>
                    <select [(ngModel)]="newContact.contact_type">
                      <option>Buyer</option>
                      <option>Influencer</option>
                      <option>Gatekeeper</option>
                      <option>Technical Validator</option>
                    </select>
                  </div>
                </div>
                <div class="form-actions">
                  <button class="btn-ghost" (click)="showContactForm = false">Cancel</button>
                  <button class="btn-primary" (click)="addContact()">Save Contact</button>
                </div>
              </div>
            }
            @for (c of contacts; track c.id) {
              <div class="card contact-card">
                <div class="contact-header">
                  <div>
                    <strong>{{ c.name }}</strong>
                    @if (c.role) { <span class="muted"> · {{ c.role }}</span> }
                  </div>
                  <span class="contact-type-badge">{{ c.contact_type }}</span>
                </div>
                <div class="contact-meta">
                  @if (c.email) { <span>{{ c.email }}</span> }
                  @if (c.linkedin_url) {
                    <a [href]="c.linkedin_url" target="_blank" class="link">LinkedIn ↗</a>
                  }
                  <span class="status-dot" [class]="outreachClass(c.outreach_status)">
                    {{ c.outreach_status }}
                  </span>
                </div>
              </div>
            }
            @if (contacts.length === 0 && !showContactForm) {
              <div class="empty-state">No contacts yet.</div>
            }
          </div>
        }

        <!-- Tasks tab -->
        @if (activeTab === 'tasks') {
          <div class="tab-content">
            <div class="tab-header">
              <h3>Tasks</h3>
              <button class="btn-primary btn-sm" (click)="showTaskForm = !showTaskForm">+ Add Task</button>
            </div>
            @if (showTaskForm) {
              <div class="inline-form card">
                <div class="form-grid">
                  <div class="field">
                    <label>Description *</label>
                    <input [(ngModel)]="newTask.description" placeholder="Task description">
                  </div>
                  <div class="field">
                    <label>Due Date</label>
                    <input type="date" [(ngModel)]="newTask.due_date_str">
                  </div>
                </div>
                <div class="form-actions">
                  <button class="btn-ghost" (click)="showTaskForm = false">Cancel</button>
                  <button class="btn-primary" (click)="addTask()">Save Task</button>
                </div>
              </div>
            }
            @for (t of tasks; track t.id) {
              <div class="card task-card" [class.done]="t.status === 'done'">
                <div class="task-row">
                  <button class="check-btn" (click)="toggleTask(t)"
                          [class.checked]="t.status === 'done'">
                    <span class="material-icons">{{ t.status === 'done' ? 'check_circle' : 'radio_button_unchecked' }}</span>
                  </button>
                  <span class="task-desc" [class.done-text]="t.status === 'done'">{{ t.description }}</span>
                  @if (t.due_date) {
                    <span class="due mono muted">{{ t.due_date | date:'d MMM' }}</span>
                  }
                </div>
              </div>
            }
            @if (tasks.length === 0 && !showTaskForm) {
              <div class="empty-state">No tasks for this company.</div>
            }
          </div>
        }

        <!-- Notes tab -->
        @if (activeTab === 'notes') {
          <div class="tab-content">
            <h3>Notes</h3>
            <textarea class="notes-area" [(ngModel)]="notesEdit" rows="10" placeholder="Internal notes..."></textarea>
            <button class="btn-primary" (click)="saveNotes()">Save Notes</button>
          </div>
        }
      }
    </div>
  `,
  styleUrl: './company-detail.component.scss',
})
export class CompanyDetailComponent implements OnInit {
  company: Company | null = null;
  research: ResearchReport[] = [];
  briefs: SignalBrief[] = [];
  contacts: Contact[] = [];
  tasks: Task[] = [];
  stages: PipelineStage[] = [];
  loading = true;
  researchRunning = false;
  showContactForm = false;
  showTaskForm = false;
  activeTab = 'research';
  stageId: number | null = null;
  notesEdit = '';

  tabs = [
    { key: 'research', label: 'Research' },
    { key: 'briefs', label: 'Signal Briefs' },
    { key: 'contacts', label: 'Contacts' },
    { key: 'tasks', label: 'Tasks' },
    { key: 'notes', label: 'Notes' },
  ];

  counts: Record<string, number> = {};

  newContact: Partial<Contact> = { contact_type: 'Buyer' };
  newTask: Partial<Task> & { due_date_str?: string } = {};

  constructor(private route: ActivatedRoute, private api: ApiService) {}

  ngOnInit(): void {
    const id = +this.route.snapshot.params['id'];
    this.api.getPipelineStages().subscribe(s => (this.stages = s));
    this.loadAll(id);
  }

  loadAll(id: number): void {
    this.api.getCompany(id).subscribe(c => {
      this.company = c;
      this.stageId = c.pipeline_stage_id || null;
      this.notesEdit = c.notes || '';
      this.loading = false;
    });
    this.api.getResearch(id).subscribe(r => {
      this.research = r;
      this.counts['research'] = r.length;
    });
    this.api.getBriefs(id).subscribe(b => {
      this.briefs = b;
      this.counts['briefs'] = b.length;
    });
    this.api.getContacts(id).subscribe(c => {
      this.contacts = c;
      this.counts['contacts'] = c.length;
    });
    this.api.getTasks(id).subscribe(t => {
      this.tasks = t;
      this.counts['tasks'] = t.filter(x => x.status === 'pending').length;
    });
  }

  updateStage(): void {
    if (!this.company) return;
    const sid = this.stageId ? +this.stageId : undefined;
    this.api.updateCompany(this.company.id, { pipeline_stage_id: sid }).subscribe();
  }

  runResearch(): void {
    if (!this.company) return;
    this.researchRunning = true;
    this.api.runResearch(this.company.id, {}).subscribe({
      next: (r) => {
        this.research = [r, ...this.research];
        this.counts['research'] = this.research.length;
        this.researchRunning = false;
      },
      error: () => (this.researchRunning = false),
    });
  }

  generateBrief(researchId: number): void {
    if (!this.company) return;
    this.api.generateBrief(this.company.id, researchId).subscribe(b => {
      this.briefs = [b, ...this.briefs];
      this.counts['briefs'] = this.briefs.length;
      this.activeTab = 'briefs';
    });
  }

  addContact(): void {
    if (!this.company || !this.newContact.name) return;
    this.api.createContact({ ...this.newContact, company_id: this.company.id }).subscribe(c => {
      this.contacts = [c, ...this.contacts];
      this.counts['contacts'] = this.contacts.length;
      this.newContact = { contact_type: 'Buyer' };
      this.showContactForm = false;
    });
  }

  addTask(): void {
    if (!this.company || !this.newTask.description) return;
    const payload: Partial<Task> = {
      company_id: this.company.id,
      description: this.newTask.description,
    };
    if (this.newTask.due_date_str) {
      payload.due_date = this.newTask.due_date_str;
    }
    this.api.createTask(payload).subscribe(t => {
      this.tasks = [...this.tasks, t];
      this.newTask = {};
      this.showTaskForm = false;
    });
  }

  toggleTask(task: Task): void {
    const newStatus = task.status === 'done' ? 'pending' : 'done';
    this.api.updateTask(task.id, { status: newStatus }).subscribe(updated => {
      const idx = this.tasks.findIndex(t => t.id === task.id);
      if (idx !== -1) this.tasks[idx] = updated;
    });
  }

  saveNotes(): void {
    if (!this.company) return;
    this.api.updateCompany(this.company.id, { notes: this.notesEdit }).subscribe();
  }

  outreachClass(status?: string): string {
    const map: Record<string, string> = {
      'Not contacted': 'status-gray',
      'Message sent': 'status-blue',
      'Replied': 'status-green',
      'Meeting booked': 'status-teal',
      'Not relevant': 'status-red',
    };
    return map[status || ''] || 'status-gray';
  }
}
