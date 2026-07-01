const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
 
class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail || res.statusText);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ---------- Auth ----------
export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  tenant_id: string;
}

export function register(
  email: string,
  password: string,
  business_name: string,
  funnel_template: string
) {
  return request<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, business_name, funnel_template }),
  });
}

export function login(email: string, password: string) {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function getMe() {
  return request<UserResponse>("/auth/me");
}

export type FunnelTemplateValue =
  | Record<string, string>
  | { name: string; funnel_config: Record<string, string> };

export type FunnelTemplateMap = Record<string, FunnelTemplateValue>;

export function getFunnelTemplates() {
  return request<FunnelTemplateMap>(
    "/auth/funnel-templates"
  );
}

// ---------- Tenant ----------
export interface TenantResponse {
  id: string;
  name: string;
  funnel_config: Record<string, string>;
}

export function getTenant() {
  return request<TenantResponse>("/tenants/me");
}

export function updateFunnel(funnel_config: Record<string, string>) {
  return request<TenantResponse>("/tenants/me/funnel", {
    method: "PUT",
    body: JSON.stringify({ funnel_config }),
  });
}

// ---------- Leads ----------
export interface LeadListItem {
  id: string;
  phone: string;
  name: string | null;
  status: string;
  current_stage: string | null;
  temperature_score: number | null;
  analysis_status: AnalysisStatus;
  analysis_error: string | null;
  is_processing: boolean;
  created_at: string;
  updated_at: string;
  conversation_time_minutes: number | null;
}

export type AnalysisStatus =
  | "idle"
  | "pending"
  | "processing"
  | "completed"
  | "failed";

export interface AnalysisSummary {
  id: string;
  temperature_score: number;
  current_stage: string | null;
  conversation_summary: string;
  qualitative_tips: string;
  suggested_reply: string;
  created_at: string;
}

export interface LeadDetail extends LeadListItem {
  latest_analysis: AnalysisSummary | null;
}

export interface LeadFilters {
  status?: string;
  stage?: string;
  min_score?: number;
  max_score?: number;
  sort_by?: string;
  order?: string;
  page?: number;
  page_size?: number;
}

export function getLeads(filters: LeadFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") params.set(k, String(v));
  });
  const qs = params.toString();
  return request<LeadListItem[]>(`/leads${qs ? `?${qs}` : ""}`);
}

export function getLead(id: string) {
  return request<LeadDetail>(`/leads/${id}`);
}

export interface MessageItem {
  id: string;
  direction: string;
  content: string;
  timestamp: string;
}

export interface PaginatedMessages {
  items: MessageItem[];
  total: number;
  page: number;
  page_size: number;
}

export function getMessages(leadId: string, page = 1, pageSize = 50) {
  return request<PaginatedMessages>(
    `/leads/${leadId}/messages?page=${page}&page_size=${pageSize}`
  );
}

export function updateLeadStatus(leadId: string, status: "converted" | "lost") {
  return request<{ status: string; lead_id: string; new_status: string }>(`/leads/${leadId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function updateLeadStage(leadId: string, current_stage: string) {
  return request<{ status: string; lead_id: string; new_stage: string }>(`/leads/${leadId}/stage`, {
    method: "PATCH",
    body: JSON.stringify({ current_stage }),
  });
}

// ---------- Analysis ----------
export interface AnalysisJobAcceptedResponse {
  lead_id: string;
  analysis_status: "pending";
}

export interface AnalyzeBatchResponse {
  total_enqueued: number;
  lead_ids?: string[];
}

export interface AnalyzeStatusCounts {
  idle: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
}

export interface AnalyzeStatusResponse {
  counts: AnalyzeStatusCounts;
  pending_ids?: string[];
  processing_ids?: string[];
  completed_ids?: string[];
  failed_ids?: string[];
}

export interface AnalysisLeadStatusResponse {
  lead_id: string;
  analysis_status: AnalysisStatus;
  analysis_error: string | null;
}

export function analyzeLead(leadId: string) {
  return request<AnalysisJobAcceptedResponse>(`/leads/${leadId}/analyze`, {
    method: "POST",
  });
}

export function analyzeAll() {
  return request<AnalyzeBatchResponse>("/leads/analyze-all", {
    method: "POST",
  });
}

export function getAnalyzeStatus(leadIds?: string[]) {
  const params = new URLSearchParams();
  leadIds?.forEach((id) => params.append("lead_ids", id));
  const qs = params.toString();
  return request<AnalyzeStatusResponse>(`/leads/analyze/status${qs ? `?${qs}` : ""}`);
}

export function getLeadAnalyzeStatus(leadId: string) {
  return request<AnalysisLeadStatusResponse>(`/leads/${leadId}/analyze/status`);
}

// ---------- Dashboard ----------
export interface DashboardStats {
  total_active: number;
  total_converted: number;
  total_lost: number;
  leads_by_stage: Record<string, number>;
  avg_temperature: number | null;
}

export function getDashboardStats() {
  return request<DashboardStats>("/dashboard/stats");
}

// ---------- WhatsApp ----------
export interface WhatsAppStatus {
  status: string;
  phone: string | null;
  connected_since: string | null;
}

export function getWhatsAppStatus() {
  return request<WhatsAppStatus>("/whatsapp/status");
}

export { ApiError };
