import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import {
  ApiService, Company, ResearchReport, SignalBrief, Contact, Task, PipelineStage,
  IntelligenceData, IntelligenceStatus, WebIntelligenceReport, ContactDiscovery,
  PublicContact,
} from '../../core/services/api.service';
import { interval, Subscription } from 'rxjs';
import { switchMap, takeWhile } from 'rxjs/operators';

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
            <!-- Intelligence scan status badge -->
            <div class="scan-status" [class]="scanStatusClass">
              @if (scanStatus === 'running' || scanStatus === 'pending') {
                <span class="pulse-dot"></span> Scanning…
              } @else if (scanStatus === 'complete') {
                <span class="status-dot green"></span> Intelligence ready
                @if (intelligenceData?.intelligence?.scan_completed_at) {
                  <span class="scan-ago">{{ timeAgo(intelligenceData!.intelligence!.scan_completed_at) }}</span>
                }
                <button class="btn-ghost btn-xs" (click)="triggerScan()" [disabled]="scanRunning">Refresh</button>
              } @else if (scanStatus === 'failed') {
                <span class="status-dot red"></span> Scan failed
                <button class="btn-ghost btn-xs danger" (click)="retryScan()">Retry</button>
              } @else {
                <span class="status-dot grey"></span> Not yet scanned
                <button class="btn-ghost btn-xs" (click)="triggerScan()">Scan now</button>
              }
            </div>

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

        <!-- ═══════════════════ INTELLIGENCE TAB ═══════════════════ -->
        @if (activeTab === 'intelligence') {
          <div class="tab-content">
            @if (scanStatus === 'running' || scanStatus === 'pending') {
              <div class="scanning-state">
                <div class="scanning-pulse"></div>
                <p>Gathering intelligence… this takes 30–60 seconds.</p>
                <p class="muted">News, SENS filings, JSE data, and web presence are being scanned in parallel.</p>
              </div>
            } @else if (scanStatus === 'failed') {
              <div class="scan-error-state">
                <span class="material-icons">error_outline</span>
                <p>Scan failed: {{ intelligenceData?.intelligence?.scan_error || 'Unknown error' }}</p>
                <button class="btn-primary btn-sm" (click)="retryScan()">Retry Scan</button>
              </div>
            } @else if (scanStatus === 'not_scanned') {
              <div class="empty-state">
                <p>No intelligence gathered yet.</p>
                <button class="btn-primary btn-sm" (click)="triggerScan()">Run Scan</button>
              </div>
            } @else if (intelligenceData?.intelligence) {

              @if (intel && intel.is_demo) {
                <div class="demo-banner">DEMO DATA — configure SERPER_API_KEY and OPENAI_API_KEY for live intelligence</div>
              }

              <!-- ── Section A: Intelligence Summary ────────────────────── -->
              @if (intel) {
              <div class="intel-section">
                <div class="intel-section-title">INTELLIGENCE SUMMARY</div>
                <p class="intel-summary">{{ intel.intelligence_summary }}</p>

                @if (intel.timing_assessment) {
                  <div class="intel-meta-row">
                    <span class="intel-label">Timing</span>
                    <span class="intel-value">{{ intel.timing_assessment }}</span>
                  </div>
                }
                @if (intel.recommended_approach) {
                  <div class="intel-meta-row">
                    <span class="intel-label">Approach</span>
                    <span class="intel-value">{{ intel.recommended_approach }}</span>
                  </div>
                }
              </div>

              <!-- ── Key Signals ─────────────────────────────────────────── -->
              @if (intel.key_signals?.length) {
                <div class="intel-section">
                  <div class="intel-section-title">KEY SIGNALS</div>
                  @for (sig of sortedSignals(intel.key_signals); track sig.signal) {
                    <div class="signal-row" [class]="'signal-' + sig.relevance">
                      <div class="signal-indicator">
                        <span class="signal-dot" [class]="'dot-' + sig.relevance"></span>
                        <span class="signal-rel">{{ sig.relevance | uppercase }}</span>
                        @if (sig.signal_type) {
                          <span class="signal-type-badge">{{ formatSignalType(sig.signal_type) }}</span>
                        }
                      </div>
                      <div class="signal-text">{{ sig.signal }}</div>
                      @if (sig.source_url) {
                        <a [href]="sig.source_url" target="_blank" class="signal-source">Source ↗</a>
                      }
                    </div>
                  }
                </div>
              }

              <!-- ── JSE Data ────────────────────────────────────────────── -->
              @if (intel.is_jse_listed && intel.latest_stock_data) {
                <div class="intel-section jse-card">
                  <div class="intel-section-title">JSE DATA</div>
                  <div class="jse-row">
                    <span class="jse-ticker">{{ intel.jse_ticker }}</span>
                    @if (intel.latest_stock_data.price) {
                      <span class="jse-price">R{{ intel.latest_stock_data.price | number:'1.2-2' }}</span>
                    }
                    @if (intel.latest_stock_data.change_pct !== null && intel.latest_stock_data.change_pct !== undefined) {
                      <span class="jse-change" [class.positive]="intel.latest_stock_data.change_pct! >= 0" [class.negative]="intel.latest_stock_data.change_pct! < 0">
                        {{ intel.latest_stock_data.change_pct! >= 0 ? '▲' : '▼' }} {{ intel.latest_stock_data.change_pct | number:'1.1-1' }}% today
                      </span>
                    }
                  </div>
                  <div class="jse-meta">
                    @if (intel.latest_stock_data.market_cap) { <span>Market cap: {{ intel.latest_stock_data.market_cap }}</span> }
                    @if (intel.latest_stock_data.week_52_high && intel.latest_stock_data.week_52_low) {
                      <span>52w: R{{ intel.latest_stock_data.week_52_low | number:'1.2-2' }} – R{{ intel.latest_stock_data.week_52_high | number:'1.2-2' }}</span>
                    }
                    @if (intel.latest_stock_data.last_updated) {
                      <span class="muted">Last updated: {{ timeAgo(intel.latest_stock_data.last_updated) }}</span>
                    }
                  </div>
                </div>
              }

              <!-- ── News & Announcements ────────────────────────────────── -->
              @if (intel.news_articles?.length || intel.sens_announcements?.length) {
                <div class="intel-section">
                  <div class="intel-section-header">
                    <div class="intel-section-title">NEWS & ANNOUNCEMENTS</div>
                    <div class="news-filters">
                      @for (f of newsFilters; track f.key) {
                        <button class="filter-btn" [class.active]="newsFilter === f.key" (click)="newsFilter = f.key">{{ f.label }}</button>
                      }
                    </div>
                  </div>
                  @for (article of filteredNews(intel); track article.url) {
                    <div class="news-row">
                      <div class="news-meta">
                        <span class="news-source">{{ article.source || 'Web' }}</span>
                        @if (article.published_at) {
                          <span class="news-date muted">· {{ article.published_at }}</span>
                        }
                      </div>
                      <div class="news-title">{{ article.title }}</div>
                      @if (article.snippet) {
                        <div class="news-snippet muted">{{ article.snippet }}</div>
                      }
                      <a [href]="article.url" target="_blank" class="news-link">Read →</a>
                    </div>
                  }
                </div>
              }

              <!-- ── Section B: Contact Discovery ───────────────────────── -->
              @if (disc) {
                <div class="intel-section">
                  <div class="intel-section-title">WHO TO TARGET AT THIS COMPANY</div>

                  @for (role of disc.recommended_roles; track role.title) {
                    <div class="role-row">
                      <div class="role-priority">{{ role.priority }}</div>
                      <div class="role-body">
                        <div class="role-title">{{ role.title }}
                          @if (role.seniority) { <span class="role-seniority">{{ role.seniority }}</span> }
                          <span class="priority-badge p{{ role.priority }}">PRIORITY {{ role.priority }}</span>
                        </div>
                        <div class="role-why">{{ role.why }}</div>
                      </div>
                    </div>
                  }
                </div>

                <!-- LinkedIn Search URLs -->
                @if (disc.linkedin_search_urls?.length) {
                  <div class="intel-section">
                    <div class="intel-section-title">FIND THEM ON LINKEDIN</div>
                    <div class="linkedin-grid">
                      @for (link of disc.linkedin_search_urls; track link.url) {
                        <a [href]="link.url" target="_blank" class="linkedin-btn">
                          <span class="material-icons" style="font-size:16px">open_in_new</span>
                          {{ link.label }}
                        </a>
                      }
                    </div>
                    <p class="linkedin-note muted">LinkedIn search URLs open in a new tab. Find the person, then add them as a contact below.</p>
                  </div>
                }

                <!-- Other Contact Sources -->
                @if (disc.contact_sources?.length) {
                  <div class="intel-section">
                    <div class="intel-section-title">OTHER SOURCES</div>
                    @for (source of disc.contact_sources; track source.url) {
                      <div class="source-row">
                        <div class="source-type-badge">{{ formatSourceType(source.source_type) }}</div>
                        <div class="source-body">
                          <div class="source-desc">{{ source.description }}</div>
                          @if (source.expected_contacts) {
                            <div class="source-expected muted">{{ source.expected_contacts }}</div>
                          }
                          @if (source.url) {
                            <a [href]="source.url" target="_blank" class="source-link">Open →</a>
                          }
                        </div>
                      </div>
                    }
                  </div>
                }

                <!-- Publicly Found Contacts -->
                @if (disc.publicly_listed_contacts?.length) {
                  <div class="intel-section">
                    <div class="intel-section-title">CONTACTS FOUND ON PUBLIC WEB</div>
                    @for (pc of disc.publicly_listed_contacts; track pc.name) {
                      <div class="found-contact-row">
                        <span class="found-confidence" [class]="'conf-' + pc.confidence">{{ pc.confidence | uppercase }}</span>
                        <div class="found-contact-body">
                          <strong>{{ pc.name }}</strong>
                          @if (pc.role) { <span class="muted"> — {{ pc.role }}</span> }
                          @if (pc.source_url) {
                            <div class="found-source">
                              Source: <a [href]="pc.source_url" target="_blank" class="link">{{ pc.source_type || 'web' }} ↗</a>
                            </div>
                          }
                        </div>
                        <button class="btn-accent btn-xs" (click)="prefillContact(pc)">Add to contacts →</button>
                      </div>
                    }
                  </div>
                }
              }
            }
          }

          </div>
        }

        <!-- ═══════════════════ RESEARCH TAB ═══════════════════════ -->
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
                @if (r.is_demo) { <div class="demo-badge">DEMO OUTPUT</div> }
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

        <!-- ═══════════════════ SIGNAL BRIEFS TAB ══════════════════ -->
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

        <!-- ═══════════════════ CONTACTS TAB ═══════════════════════ -->
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
                  <button class="btn-ghost" (click)="cancelContactForm()">Cancel</button>
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

        <!-- ═══════════════════ TASKS TAB ═══════════════════════════ -->
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
                  <button class="check-btn" (click)="toggleTask(t)" [class.checked]="t.status === 'done'">
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

        <!-- ═══════════════════ NOTES TAB ═══════════════════════════ -->
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
export class CompanyDetailComponent implements OnInit, OnDestroy {
  company: Company | null = null;
  research: ResearchReport[] = [];
  briefs: SignalBrief[] = [];
  contacts: Contact[] = [];
  tasks: Task[] = [];
  stages: PipelineStage[] = [];
  intelligenceData: IntelligenceData | null = null;
  scanStatus: IntelligenceStatus['status'] = 'not_scanned';
  scanRunning = false;

  loading = true;
  researchRunning = false;
  showContactForm = false;
  showTaskForm = false;
  activeTab = 'intelligence';
  stageId: number | null = null;
  notesEdit = '';
  newsFilter: 'all' | '7d' | '30d' = 'all';

  tabs = [
    { key: 'intelligence', label: 'Intelligence' },
    { key: 'research', label: 'Research' },
    { key: 'briefs', label: 'Signal Briefs' },
    { key: 'contacts', label: 'Contacts' },
    { key: 'tasks', label: 'Tasks' },
    { key: 'notes', label: 'Notes' },
  ];

  newsFilters: { key: 'all' | '7d' | '30d'; label: string }[] = [
    { key: 'all', label: 'All' },
    { key: '30d', label: '30 days' },
    { key: '7d', label: '7 days' },
  ];

  counts: Record<string, number> = {};
  newContact: Partial<Contact> = { contact_type: 'Buyer' };
  newTask: Partial<Task> & { due_date_str?: string } = {};

  private companyId = 0;
  private pollSub?: Subscription;

  constructor(private route: ActivatedRoute, private api: ApiService) {}

  ngOnInit(): void {
    this.companyId = +this.route.snapshot.params['id'];
    this.api.getPipelineStages().subscribe(s => (this.stages = s));
    this.loadAll(this.companyId);
  }

  ngOnDestroy(): void {
    this.pollSub?.unsubscribe();
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
    this.loadIntelligence(id);
  }

  loadIntelligence(id: number): void {
    this.api.getIntelligenceStatus(id).subscribe(status => {
      this.scanStatus = status.status;
      if (status.status === 'complete' || status.status === 'failed') {
        this.api.getIntelligence(id).subscribe(data => (this.intelligenceData = data));
      } else if (status.status === 'running' || status.status === 'pending') {
        this.startPolling(id);
      }
    });
  }

  startPolling(id: number): void {
    this.pollSub?.unsubscribe();
    this.pollSub = interval(4000)
      .pipe(
        switchMap(() => this.api.getIntelligenceStatus(id)),
        takeWhile(s => s.status === 'running' || s.status === 'pending', true),
      )
      .subscribe(status => {
        this.scanStatus = status.status;
        if (status.status === 'complete' || status.status === 'failed') {
          this.api.getIntelligence(id).subscribe(data => (this.intelligenceData = data));
          this.pollSub?.unsubscribe();
        }
      });
  }

  triggerScan(): void {
    this.scanRunning = true;
    this.api.triggerIntelligenceScan(this.companyId).subscribe({
      next: () => {
        this.scanStatus = 'pending';
        this.scanRunning = false;
        this.startPolling(this.companyId);
      },
      error: (err) => {
        const msg = err?.error?.detail || 'Failed to start scan';
        alert(msg);
        this.scanRunning = false;
      },
    });
  }

  retryScan(): void {
    this.api.retryIntelligenceScan(this.companyId).subscribe(() => {
      this.scanStatus = 'pending';
      this.startPolling(this.companyId);
    });
  }

  // ── Getters (Angular 17 compatible — no @let) ────────────────────────────

  get intel(): WebIntelligenceReport | null {
    return this.intelligenceData?.intelligence ?? null;
  }

  get disc(): ContactDiscovery | null {
    return this.intelligenceData?.discovery ?? null;
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  get scanStatusClass(): string {
    if (this.scanStatus === 'running' || this.scanStatus === 'pending') return 'scan-running';
    if (this.scanStatus === 'complete') return 'scan-complete';
    if (this.scanStatus === 'failed') return 'scan-failed';
    return 'scan-idle';
  }

  sortedSignals(signals: any[]): any[] {
    const order = { high: 0, medium: 1, low: 2 };
    return [...signals].sort((a, b) => (order[a.relevance as keyof typeof order] ?? 3) - (order[b.relevance as keyof typeof order] ?? 3));
  }

  filteredNews(intel: WebIntelligenceReport): any[] {
    const all = [...(intel.news_articles || []), ...(intel.sens_announcements || [])];
    return all.slice(0, 15);
  }

  formatSignalType(t: string): string {
    return t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  formatSourceType(t: string): string {
    const map: Record<string, string> = {
      company_website: 'Website',
      annual_report: 'Annual Report',
      sens_announcement: 'SENS',
      leadership_page: 'Leadership Page',
      news_article: 'News',
    };
    return map[t] || t;
  }

  timeAgo(iso?: string): string {
    if (!iso) return '';
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  }

  prefillContact(pc: PublicContact): void {
    const parts = pc.name.trim().split(/\s+/);
    const firstName = parts[0] || '';
    const lastName = parts.slice(1).join(' ');
    this.newContact = {
      name: pc.name,
      role: pc.role || '',
      contact_type: 'Buyer',
      company_id: this.companyId,
    };
    this.showContactForm = true;
    this.activeTab = 'contacts';
  }

  cancelContactForm(): void {
    this.showContactForm = false;
    this.newContact = { contact_type: 'Buyer' };
  }

  // ── Existing actions ────────────────────────────────────────────────────────

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
    if (this.newTask.due_date_str) payload.due_date = this.newTask.due_date_str;
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
