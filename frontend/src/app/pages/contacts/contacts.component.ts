import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService, Contact, Company } from '../../core/services/api.service';

@Component({
  selector: 'app-contacts',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Contacts</h2>
          <span class="subtitle">{{ contacts.length }} total</span>
        </div>
        <button class="btn-primary" (click)="showForm = !showForm">
          <span class="material-icons">person_add</span> Add Contact
        </button>
      </div>

      @if (showForm) {
        <div class="card form-card">
          <h3>New Contact</h3>
          <div class="form-grid">
            <div class="field">
              <label>Company *</label>
              <select [(ngModel)]="newContact.company_id">
                <option [value]="null">— Select company —</option>
                @for (c of companies; track c.id) {
                  <option [value]="c.id">{{ c.name }}</option>
                }
              </select>
            </div>
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
            <div class="field">
              <label>Outreach Status</label>
              <select [(ngModel)]="newContact.outreach_status">
                <option>Not contacted</option>
                <option>Message sent</option>
                <option>Replied</option>
                <option>Meeting booked</option>
                <option>Not relevant</option>
              </select>
            </div>
          </div>
          <div class="form-actions">
            <button class="btn-ghost" (click)="showForm = false; resetForm()">Cancel</button>
            <button class="btn-primary" (click)="save()" [disabled]="!newContact.name || !newContact.company_id">Save</button>
          </div>
        </div>
      }

      @if (loading) {
        <div class="loading">Loading...</div>
      } @else if (contacts.length === 0) {
        <div class="empty-state">
          <span class="material-icons">contacts</span>
          <p>No contacts yet.</p>
        </div>
      } @else {
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Role</th>
                <th>Company</th>
                <th>Type</th>
                <th>Status</th>
                <th>Email</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              @for (c of contacts; track c.id) {
                <tr>
                  <td class="font-medium">{{ c.name }}</td>
                  <td class="muted">{{ c.role || '—' }}</td>
                  <td>
                    <a [routerLink]="['/companies', c.company_id]" class="link">
                      {{ companyName(c.company_id) }}
                    </a>
                  </td>
                  <td><span class="type-badge">{{ c.contact_type }}</span></td>
                  <td>
                    <span class="status-dot" [class]="statusClass(c.outreach_status)">
                      {{ c.outreach_status }}
                    </span>
                  </td>
                  <td class="muted mono">{{ c.email || '—' }}</td>
                  <td>
                    <select class="status-select" [(ngModel)]="c.outreach_status" (ngModelChange)="updateStatus(c)">
                      <option>Not contacted</option>
                      <option>Message sent</option>
                      <option>Replied</option>
                      <option>Meeting booked</option>
                      <option>Not relevant</option>
                    </select>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
  styleUrl: './contacts.component.scss',
})
export class ContactsComponent implements OnInit {
  contacts: Contact[] = [];
  companies: Company[] = [];
  loading = true;
  showForm = false;
  newContact: Partial<Contact> = { contact_type: 'Buyer', outreach_status: 'Not contacted' };

  private companyMap: Map<number, string> = new Map();

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getCompanies().subscribe(cs => {
      this.companies = cs;
      cs.forEach(c => this.companyMap.set(c.id, c.name));
    });
    this.load();
  }

  load(): void {
    this.api.getContacts().subscribe({
      next: (cs) => { this.contacts = cs; this.loading = false; },
      error: () => (this.loading = false),
    });
  }

  save(): void {
    if (!this.newContact.name || !this.newContact.company_id) return;
    this.api.createContact(this.newContact).subscribe(c => {
      this.contacts = [c, ...this.contacts];
      this.showForm = false;
      this.resetForm();
    });
  }

  updateStatus(contact: Contact): void {
    this.api.updateContact(contact.id, { outreach_status: contact.outreach_status }).subscribe();
  }

  companyName(id: number): string {
    return this.companyMap.get(id) || `Company ${id}`;
  }

  resetForm(): void {
    this.newContact = { contact_type: 'Buyer', outreach_status: 'Not contacted' };
  }

  statusClass(status?: string): string {
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
