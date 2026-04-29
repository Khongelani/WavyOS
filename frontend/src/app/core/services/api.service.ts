import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Company {
  id: number;
  name: string;
  industry?: string;
  website?: string;
  country?: string;
  notes?: string;
  status?: string;
  pipeline_stage_id?: number;
  pipeline_stage?: PipelineStage;
  created_at: string;
  updated_at: string;
  research_count?: number;
  brief_count?: number;
  contact_count?: number;
}

export interface PipelineStage {
  id: number;
  name: string;
  order_index: number;
  color: string;
}

export interface Contact {
  id: number;
  company_id: number;
  name: string;
  role?: string;
  email?: string;
  linkedin_url?: string;
  contact_type?: string;
  notes?: string;
  outreach_status?: string;
  created_at: string;
}

export interface ResearchReport {
  id: number;
  company_id: number;
  overview?: string;
  signals?: string[];
  cashflow_pressures?: string[];
  buyer_personas?: { title: string; why: string }[];
  outreach_angle?: string;
  confidence_score?: number;
  source_links?: string[];
  is_demo: boolean;
  created_at: string;
}

export interface SignalBrief {
  id: number;
  company_id: number;
  research_id?: number;
  executive_signal?: string;
  why_it_matters?: string;
  receivables_blind_spots?: string[];
  operational_impact?: string;
  suggested_action?: string;
  conversation_opener?: string;
  is_edited: boolean;
  is_demo: boolean;
  created_at: string;
}

export interface OutreachDraft {
  id: number;
  contact_id?: number;
  company_id?: number;
  brief_id?: number;
  linkedin_message?: string;
  email_subject?: string;
  email_body?: string;
  followup_message?: string;
  gatekeeper_version?: string;
  technical_validator_version?: string;
  status?: string;
  marked_sent_at?: string;
  followup_due_at?: string;
  contact_status_after?: string;
  is_demo: boolean;
  created_at: string;
}

export interface Task {
  id: number;
  company_id?: number;
  contact_id?: number;
  description: string;
  due_date?: string;
  status?: string;
  task_type?: string;
  is_demo: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_companies: number;
  companies_researched: number;
  contacts_added: number;
  outreach_drafts: number;
  calls_booked: number;
  briefs_generated: number;
  pipeline_value: string;
  today_tasks: Task[];
}

export interface PipelineColumn {
  stage: PipelineStage;
  companies: Partial<Company>[];
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // Companies
  getCompanies(search?: string, stageId?: number): Observable<Company[]> {
    let params = new HttpParams();
    if (search) params = params.set('search', search);
    if (stageId) params = params.set('stage_id', stageId.toString());
    return this.http.get<Company[]>(`${this.base}/companies`, { params });
  }

  createCompany(data: Partial<Company>): Observable<Company> {
    return this.http.post<Company>(`${this.base}/companies`, data);
  }

  getCompany(id: number): Observable<Company> {
    return this.http.get<Company>(`${this.base}/companies/${id}`);
  }

  updateCompany(id: number, data: Partial<Company>): Observable<Company> {
    return this.http.put<Company>(`${this.base}/companies/${id}`, data);
  }

  deleteCompany(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/companies/${id}`);
  }

  // Research
  getResearch(companyId: number): Observable<ResearchReport[]> {
    return this.http.get<ResearchReport[]>(`${this.base}/companies/${companyId}/research`);
  }

  runResearch(companyId: number, data: { company_name?: string; website?: string; industry?: string }): Observable<ResearchReport> {
    return this.http.post<ResearchReport>(`${this.base}/companies/${companyId}/research`, data);
  }

  // Signal Briefs
  getBriefs(companyId: number): Observable<SignalBrief[]> {
    return this.http.get<SignalBrief[]>(`${this.base}/companies/${companyId}/briefs`);
  }

  generateBrief(companyId: number, researchId: number): Observable<SignalBrief> {
    return this.http.post<SignalBrief>(`${this.base}/companies/${companyId}/briefs`, { research_id: researchId });
  }

  updateBrief(companyId: number, briefId: number, data: Partial<SignalBrief>): Observable<SignalBrief> {
    return this.http.put<SignalBrief>(`${this.base}/companies/${companyId}/briefs/${briefId}`, data);
  }

  // Contacts
  getContacts(companyId?: number): Observable<Contact[]> {
    let params = new HttpParams();
    if (companyId) params = params.set('company_id', companyId.toString());
    return this.http.get<Contact[]>(`${this.base}/contacts`, { params });
  }

  createContact(data: Partial<Contact>): Observable<Contact> {
    return this.http.post<Contact>(`${this.base}/contacts`, data);
  }

  updateContact(id: number, data: Partial<Contact>): Observable<Contact> {
    return this.http.put<Contact>(`${this.base}/contacts/${id}`, data);
  }

  deleteContact(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/contacts/${id}`);
  }

  // Outreach
  generateOutreach(data: { contact_id: number; company_id: number; brief_id?: number; tone?: string }): Observable<OutreachDraft> {
    return this.http.post<OutreachDraft>(`${this.base}/outreach/generate`, data);
  }

  // Pipeline
  getPipeline(): Observable<PipelineColumn[]> {
    return this.http.get<PipelineColumn[]>(`${this.base}/pipeline`);
  }

  getPipelineStages(): Observable<PipelineStage[]> {
    return this.http.get<PipelineStage[]>(`${this.base}/pipeline/stages`);
  }

  // Tasks
  getTasks(companyId?: number, status?: string): Observable<Task[]> {
    let params = new HttpParams();
    if (companyId) params = params.set('company_id', companyId.toString());
    if (status) params = params.set('status_filter', status);
    return this.http.get<Task[]>(`${this.base}/tasks`, { params });
  }

  createTask(data: Partial<Task>): Observable<Task> {
    return this.http.post<Task>(`${this.base}/tasks`, data);
  }

  updateTask(id: number, data: Partial<Task>): Observable<Task> {
    return this.http.put<Task>(`${this.base}/tasks/${id}`, data);
  }

  // Dashboard
  getDashboardStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${this.base}/dashboard/stats`);
  }

  // Admin
  getHealth(): Observable<{ api: string; database: string; ai: string }> {
    return this.http.get<{ api: string; database: string; ai: string }>(`${this.base}/admin/health`);
  }

  exportCsv(entity: string): Observable<Blob> {
    return this.http.get(`${this.base}/admin/export/${entity}`, { responseType: 'blob' });
  }

  clearDemoData(): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.base}/admin/demo-data`);
  }
}
