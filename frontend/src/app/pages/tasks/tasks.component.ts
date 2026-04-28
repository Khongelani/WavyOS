import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService, Task, Company } from '../../core/services/api.service';

@Component({
  selector: 'app-tasks',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Tasks</h2>
          <span class="subtitle">{{ pending }} pending</span>
        </div>
        <button class="btn-primary" (click)="showForm = !showForm">
          <span class="material-icons">add</span> Add Task
        </button>
      </div>

      <!-- Filter tabs -->
      <div class="filter-tabs">
        <button [class.active]="filter === 'pending'" (click)="setFilter('pending')">Pending</button>
        <button [class.active]="filter === 'done'" (click)="setFilter('done')">Done</button>
        <button [class.active]="filter === ''" (click)="setFilter('')">All</button>
      </div>

      @if (showForm) {
        <div class="card form-card">
          <div class="form-grid">
            <div class="field">
              <label>Description *</label>
              <input [(ngModel)]="newTask.description" placeholder="Task description...">
            </div>
            <div class="field">
              <label>Company</label>
              <select [(ngModel)]="newTask.company_id">
                <option [value]="null">— None —</option>
                @for (c of companies; track c.id) {
                  <option [value]="c.id">{{ c.name }}</option>
                }
              </select>
            </div>
            <div class="field">
              <label>Due Date</label>
              <input type="date" [(ngModel)]="dueDateStr">
            </div>
          </div>
          <div class="form-actions">
            <button class="btn-ghost" (click)="showForm = false">Cancel</button>
            <button class="btn-primary" (click)="create()" [disabled]="!newTask.description">Add Task</button>
          </div>
        </div>
      }

      @if (loading) {
        <div class="loading">Loading tasks...</div>
      } @else if (tasks.length === 0) {
        <div class="empty-state">
          <span class="material-icons">check_circle</span>
          <p>{{ filter === 'done' ? 'No completed tasks.' : 'No pending tasks.' }}</p>
        </div>
      } @else {
        <div class="task-list">
          @for (t of tasks; track t.id) {
            <div class="task-card" [class.done]="t.status === 'done'">
              <button class="check-btn" (click)="toggle(t)" [class.checked]="t.status === 'done'">
                <span class="material-icons">{{ t.status === 'done' ? 'check_circle' : 'radio_button_unchecked' }}</span>
              </button>
              <div class="task-body">
                <div class="task-desc" [class.strikethrough]="t.status === 'done'">{{ t.description }}</div>
                <div class="task-meta">
                  @if (t.company_id) {
                    <a [routerLink]="['/companies', t.company_id]" class="task-company">
                      {{ companyName(t.company_id) }}
                    </a>
                  }
                  @if (t.due_date) {
                    <span class="task-due mono" [class.overdue]="isOverdue(t.due_date) && t.status !== 'done'">
                      {{ t.due_date | date:'d MMM yyyy' }}
                    </span>
                  }
                  @if (t.is_demo) {
                    <span class="demo-tag">DEMO</span>
                  }
                </div>
              </div>
              <button class="dismiss-btn" (click)="dismiss(t)" title="Dismiss">
                <span class="material-icons">close</span>
              </button>
            </div>
          }
        </div>
      }
    </div>
  `,
  styleUrl: './tasks.component.scss',
})
export class TasksComponent implements OnInit {
  tasks: Task[] = [];
  companies: Company[] = [];
  loading = true;
  showForm = false;
  filter = 'pending';
  newTask: Partial<Task> = {};
  dueDateStr = '';

  private companyMap = new Map<number, string>();

  get pending(): number {
    return this.tasks.filter(t => t.status === 'pending').length;
  }

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getCompanies().subscribe(cs => {
      this.companies = cs;
      cs.forEach(c => this.companyMap.set(c.id, c.name));
    });
    this.load();
  }

  load(): void {
    this.loading = true;
    this.api.getTasks(undefined, this.filter || undefined).subscribe({
      next: (ts) => { this.tasks = ts; this.loading = false; },
      error: () => (this.loading = false),
    });
  }

  setFilter(f: string): void {
    this.filter = f;
    this.load();
  }

  create(): void {
    if (!this.newTask.description) return;
    const payload: Partial<Task> = { ...this.newTask };
    if (this.dueDateStr) payload.due_date = this.dueDateStr;
    this.api.createTask(payload).subscribe(t => {
      if (!this.filter || this.filter === t.status) {
        this.tasks = [t, ...this.tasks];
      }
      this.newTask = {};
      this.dueDateStr = '';
      this.showForm = false;
    });
  }

  toggle(task: Task): void {
    const newStatus = task.status === 'done' ? 'pending' : 'done';
    this.api.updateTask(task.id, { status: newStatus }).subscribe(() => this.load());
  }

  dismiss(task: Task): void {
    this.api.updateTask(task.id, { status: 'dismissed' }).subscribe(() => this.load());
  }

  companyName(id: number): string {
    return this.companyMap.get(id) || '';
  }

  isOverdue(dateStr: string): boolean {
    return new Date(dateStr) < new Date();
  }
}
