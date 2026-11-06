/**
 * SIH 2026 — PS26103 | Typed API Client
 * =====================================
 * Axios client wired to FastAPI backend with typed models, request interceptor
 * for JWT token propagation, and helper methods.
 */

import axios from 'axios';

export interface User {
  id: number;
  email: string;
  full_name?: string | null;
  role: string;
  ministry_scope?: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface DashboardSummary {
  latest_report_month: string | null;
  total_projects: number;
  active_scored_projects: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  rule_triggered_count: number;
  active_alerts_count: number;
  total_original_cost_cr: number;
  total_revised_cost_cr: number;
  total_expenditure_cr: number;
  cost_overrun_pct: number;
  avg_schedule_delay_months: number;
  risk_distribution: {
    High: number;
    Medium: number;
    Low: number;
  };
}

export interface MinistryBreakdown {
  ministry: string;
  total_projects: number;
  scored_projects: number;
  high_risk_count: number;
  med_risk_count: number;
  low_risk_count: number;
  avg_risk_score: number;
  total_original_cost_cr: number;
  total_revised_cost_cr: number;
}

export interface StateBreakdown {
  state: string;
  total_projects: number;
  scored_projects: number;
  high_risk_count: number;
  med_risk_count: number;
  low_risk_count: number;
  avg_risk_score: number;
  total_original_cost_cr: number;
}

export interface RiskTrendPoint {
  report_month: string;
  High: number;
  Medium: number;
  Low: number;
}

export interface ProjectListItem {
  project_uid: string;
  project_name: string;
  ministry: string;
  sector: string;
  state?: string | null;
  original_cost_cr?: number | null;
  revised_cost_cr?: number | null;
  expenditure_cr?: number | null;
  physical_progress_pct?: number | null;
  schedule_delay_months?: number | null;
  progress_stagnation_streak: number;
  risk_score: number;
  risk_band: 'High' | 'Medium' | 'Low' | string;
  ml_risk_score?: number | null;
  rule_score?: number | null;
  rule_triggered: boolean;
  shap_explanation: string;
}

export interface ProjectListResponse {
  items: ProjectListItem[];
  total: number;
  limit: number;
  offset: number;
  report_month?: string | null;
}

export interface ProjectFilters {
  ministry?: string;
  sector?: string;
  state?: string;
  risk_band?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface ProjectMetrics {
  report_month?: string | null;
  revised_cost_cr?: number | null;
  expenditure_cr?: number | null;
  physical_progress_pct?: number | null;
  schedule_delay_months?: number | null;
  progress_stagnation_streak: number;
  cost_revision_count: number;
  outlier_flag: boolean;
}

export interface ProjectRiskDetail {
  risk_score?: number | null;
  risk_band: string;
  ml_risk_score?: number | null;
  rule_score?: number | null;
  rule_triggered: boolean;
  cost_risk_prob?: number | null;
  delay_risk_prob?: number | null;
  shap_explanation?: string | null;
  model_version: string;
}

export interface ExplanationItem {
  feature_name: string;
  shap_value: number;
  explanation_text?: string | null;
}

export interface AlertItem {
  id: number;
  project_uid?: string | null;
  project_name?: string | null;
  ministry?: string | null;
  sector?: string | null;
  state?: string | null;
  report_month?: string | null;
  alert_type: string;
  severity: string;
  reason: string;
  created_at?: string | null;
  acknowledged: boolean;
}

export interface ProjectRiskResponse {
  project_uid: string;
  project_name: string;
  ministry: string;
  sector: string;
  state?: string | null;
  implementing_agency?: string | null;
  original_cost_cr?: number | null;
  approval_date?: string | null;
  start_date?: string | null;
  original_completion_date?: string | null;
  latest_metrics: ProjectMetrics;
  risk_assessment: ProjectRiskDetail;
  explanations: ExplanationItem[];
  alerts: AlertItem[];
}

export interface ProjectHistoryItem {
  report_month: string;
  revised_cost_cr?: number | null;
  expenditure_cr?: number | null;
  physical_progress_pct?: number | null;
  schedule_delay_months?: number | null;
  progress_stagnation_streak: number;
  risk_score?: number | null;
  risk_band?: string | null;
  rule_triggered: boolean;
}

export interface AlertListResponse {
  items: AlertItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface AlertSummary {
  total_active_alerts: number;
  by_severity: {
    High: number;
    Medium: number;
    Low: number;
  };
  by_type: Record<string, number>;
}

export interface AlertAcknowledgeResponse {
  id: number;
  project_uid: string;
  acknowledged: boolean;
  acknowledged_at: string;
}

// ----------------------------------------------------------------------
// Axios Client Setup
// ----------------------------------------------------------------------

export const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatically inject JWT Bearer token if present
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('paimana_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ----------------------------------------------------------------------
// API Call Functions
// ----------------------------------------------------------------------

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/login', credentials);
  if (data.access_token) {
    localStorage.setItem('paimana_token', data.access_token);
    localStorage.setItem('paimana_user', JSON.stringify(data.user));
  }
  return data;
}

export function logout(): void {
  localStorage.removeItem('paimana_token');
  localStorage.removeItem('paimana_user');
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>('/auth/me');
  return data;
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await apiClient.get<DashboardSummary>('/dashboard/summary');
  return data;
}

export async function fetchMinistryBreakdown(): Promise<MinistryBreakdown[]> {
  const { data } = await apiClient.get<MinistryBreakdown[]>('/dashboard/ministry-breakdown');
  return data;
}

export async function fetchRiskTrend(): Promise<RiskTrendPoint[]> {
  const { data } = await apiClient.get<RiskTrendPoint[]>('/dashboard/risk-trend');
  return data;
}

export async function fetchProjects(filters: ProjectFilters = {}): Promise<ProjectListResponse> {
  const { data } = await apiClient.get<ProjectListResponse>('/projects', { params: filters });
  return data;
}

export async function fetchProjectRisk(uid: string): Promise<ProjectRiskResponse> {
  const { data } = await apiClient.get<ProjectRiskResponse>(`/projects/${encodeURIComponent(uid)}/risk`);
  return data;
}

export async function fetchProjectHistory(uid: string): Promise<ProjectHistoryItem[]> {
  const { data } = await apiClient.get<ProjectHistoryItem[]>(`/projects/${encodeURIComponent(uid)}/history`);
  return data;
}

export async function fetchAlerts(params: {
  severity?: string;
  alert_type?: string;
  ministry?: string;
  acknowledged?: boolean;
  limit?: number;
  offset?: number;
} = {}): Promise<AlertListResponse> {
  const { data } = await apiClient.get<AlertListResponse>('/alerts', { params });
  return data;
}

export async function fetchAlertSummary(): Promise<AlertSummary> {
  const { data } = await apiClient.get<AlertSummary>('/alerts/summary');
  return data;
}

export async function acknowledgeAlert(id: number): Promise<AlertAcknowledgeResponse> {
  const { data } = await apiClient.patch<AlertAcknowledgeResponse>(`/alerts/${id}/acknowledge`);
  return data;
}

export async function triggerIngestion(): Promise<{ status: string; message: string }> {
  const { data } = await apiClient.post('/admin/ingest');
  return data;
}

export async function triggerRetraining(): Promise<{ status: string; message: string }> {
  const { data } = await apiClient.post('/admin/retrain');
  return data;
}

export async function fetchIngestionLogs(): Promise<any[]> {
  const { data } = await apiClient.get('/admin/ingestion-logs');
  return data;
}

export async function fetchStateBreakdown(): Promise<StateBreakdown[]> {
  const { data } = await apiClient.get<StateBreakdown[]>('/dashboard/state-breakdown');
  return data;
}

export async function fetchDataQuality(): Promise<any> {
  const { data } = await apiClient.get('/admin/data-quality');
  return data;
}

export async function fetchSystemUsers(): Promise<User[]> {
  const { data } = await apiClient.get<User[]>('/admin/users');
  return data;
}

