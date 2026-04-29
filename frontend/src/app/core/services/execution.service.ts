import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface WeeklySnapshot {
  id: number;
  week_start_date: string;
  messages_sent: number;
  followups_sent: number;
  briefs_sent: number;
  calls_requested: number;
  replies_received: number;
  companies_researched: number;
  created_at: string;
  updated_at: string;
}

export interface Alert {
  id: string;
  text: string;
  priority: number;
}

export interface MarkSentResult {
  id: number;
  status: string;
  marked_sent_at?: string;
  followup_due_at?: string;
  contact_status_after?: string;
}

export interface WeeklyReview {
  id: number;
  week_start_date: string;
  what_was_sent?: string;
  who_replied?: string;
  what_worked?: string;
  industry_response?: string;
  change_next_week?: string;
  generated_targets?: string[];
  generated_angle?: string;
  top_followups?: { contact: string; company: string; reason: string }[];
  created_at: string;
  updated_at: string;
}

export interface SprintCompany {
  id: number;
  name: string;
  industry?: string;
  country?: string;
  pipeline_stage_id?: number;
  pipeline_stage_name?: string;
  pipeline_stage_color?: string;
  days_in_stage: number;
  last_task_due?: string;
  needs_action: boolean;
  updated_at: string;
}

export interface SprintSummary {
  active_companies: number;
  need_action: number;
  moved_forward_this_week: number;
  companies: SprintCompany[];
}

@Injectable({ providedIn: 'root' })
export class ExecutionService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getCurrentSnapshot(): Observable<WeeklySnapshot> {
    return this.http.get<WeeklySnapshot>(`${this.base}/execution/snapshot/current`);
  }

  getSnapshotHistory(): Observable<WeeklySnapshot[]> {
    return this.http.get<WeeklySnapshot[]>(`${this.base}/execution/snapshot/history`);
  }

  incrementField(field: string): Observable<{ incremented: string }> {
    return this.http.patch<{ incremented: string }>(
      `${this.base}/execution/snapshot/increment`,
      { field },
    );
  }

  getAlerts(): Observable<Alert[]> {
    return this.http.get<Alert[]>(`${this.base}/execution/alerts`);
  }

  markDraftSent(draftId: number): Observable<MarkSentResult> {
    return this.http.put<MarkSentResult>(
      `${this.base}/execution/outreach/${draftId}/mark-sent`,
      {},
    );
  }

  markBriefSent(briefId: number): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(
      `${this.base}/execution/briefs/${briefId}/mark-sent`,
      {},
    );
  }

  getCurrentReview(): Observable<WeeklyReview> {
    return this.http.get<WeeklyReview>(`${this.base}/execution/review/current`);
  }

  updateReview(data: Partial<WeeklyReview>): Observable<WeeklyReview> {
    return this.http.put<WeeklyReview>(`${this.base}/execution/review/current`, data);
  }

  generateReview(whatWorked: string, industryResponse: string): Observable<WeeklyReview> {
    return this.http.post<WeeklyReview>(`${this.base}/execution/review/generate`, {
      what_worked: whatWorked,
      industry_response: industryResponse,
    });
  }

  getSprintCompanies(): Observable<SprintSummary> {
    return this.http.get<SprintSummary>(`${this.base}/sprint/companies`);
  }
}
