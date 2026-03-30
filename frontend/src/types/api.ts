// API 基础 URL
export const API_BASE_URL = 'http://localhost:8000';

// API 类型定义
export interface Email {
  id: string;
  from_address: string;
  from?: string; // 兼容旧字段
  subject: string;
  preview: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'processing' | 'completed' | 'new' | 'done';
  received_at: string;
  time?: string; // 兼容旧字段
  region: string;
}

export interface AnalysisField {
  label: string;
  value: string;
}

export interface AnalysisSection {
  title: string;
  badge: string;
  fields: AnalysisField[];
}

export interface Agent {
  name: string;
  agent_name?: string; // 兼容后端字段
  status: 'Running' | 'Completed' | 'Pending' | 'running' | 'completed' | 'pending';
  budget: number;
  budget_allocated?: number; // 兼容后端字段
  budgetMax: number;
  description?: string;
}

export interface AgentsStatusResponse {
  ceo_agent_status: string;
  sub_agents: Agent[];
  total_budget: number;
  total_spent: number;
  budget_utilization: number;
}

export interface Metric {
  name: string;
  value: string;
  trend: string;
  trendUp?: boolean;
}

export interface TraceSpan {
  name: string;
  time: string;
  duration: string;
  color: string;
}

export interface PromptVersion {
  name: string;
  score: string;
  changes: { type: 'add' | 'remove'; text: string }[];
}

// API 响应类型
export interface EmailsResponse {
  emails: Email[];
}

export interface AnalysisResponse {
  sections: AnalysisSection[];
}

export interface AgentsStatusResponse {
  agents: Agent[];
}

export interface MetricsResponse {
  metrics: Metric[];
}

export interface TracesResponse {
  spans: TraceSpan[];
}

export interface PromptVersionsResponse {
  versions: PromptVersion[];
}
