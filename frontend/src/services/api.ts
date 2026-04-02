// API 基础 URL
const API_BASE_URL = '/api';

// 从 types/api.ts 导入类型
import type {
  EmailsResponse,
  AnalysisResponse,
  AgentsStatusResponse,
  MetricsResponse as MetricsResponseType,
  TracesResponse,
  PromptVersionsResponse as PromptVersionsResponseType,
} from '../types/api';

// API 响应类型别名（与 T1 定义匹配）
export type EmailListResponse = EmailsResponse;
export type EmailAnalysisResponse = AnalysisResponse;
export type AgentStatusResponse = AgentsStatusResponse;
export type MetricsResponse = MetricsResponseType;
export type TraceResponse = TracesResponse['spans'][number];
export type PromptVersionsResponse = PromptVersionsResponseType;

/**
 * 通用的 fetch 请求函数，带错误处理
 */
async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// ==================== Email API ====================

/**
 * 获取邮件列表
 * @param status 可选的邮件状态过滤
 * @param limit 可选的数量限制
 */
export async function getEmails(
  status?: string,
  limit?: number
): Promise<EmailListResponse> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (limit) params.append('limit', limit.toString());

  const queryString = params.toString();
  const endpoint = queryString ? `/emails?${queryString}` : '/emails';

  return request<EmailListResponse>(endpoint);
}

/**
 * 获取单个邮件的分析结果
 * @param emailId 邮件 ID
 */
export async function getEmailAnalysis(
  emailId: string
): Promise<EmailAnalysisResponse> {
  return request<EmailAnalysisResponse>(`/emails/${emailId}/analysis`);
}

// ==================== Agent API ====================

/**
 * 获取所有代理的状态
 */
export async function getAgentsStatus(): Promise<AgentStatusResponse> {
  return request<AgentStatusResponse>('/agents/status');
}

// ==================== Metrics API ====================

/**
 * 获取指标数据
 */
export async function getMetrics(): Promise<MetricsResponse> {
  return request<MetricsResponse>('/metrics');
}

// ==================== Trace API ====================

/**
 * 获取追踪数据
 * @param limit 可选的数量限制
 */
export async function getTraces(limit?: number): Promise<TraceResponse[]> {
  const params = new URLSearchParams();
  if (limit) params.append('limit', limit.toString());

  const queryString = params.toString();
  const endpoint = queryString ? `/traces?${queryString}` : '/traces';

  const response = await request<TracesResponse>(endpoint);
  return response.spans;
}

// ==================== Prompt API ====================

/**
 * 获取提示词版本列表
 */
export async function getPromptVersions(): Promise<PromptVersionsResponse> {
  return request<PromptVersionsResponse>('/prompts/versions');
}

// ==================== Workflow API ====================

/**
 * 工作流响应类型
 */
export interface WorkflowHistoryItem {
  id: number;
  workflow_id: number;
  from_state: string;
  to_state: string;
  triggeredBy: string;
  reason: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface WorkflowResponse {
  id: number;
  email_id: string;
  current_state: string;
  requires_approval: boolean;
  approval_reason: string | null;
  approval_amount: number | null;
  created_at: string;
  updated_at: string;
  history: WorkflowHistoryItem[];
}

/**
 * 获取邮件工作流详情
 * @param emailId 邮件 ID
 */
export async function getEmailWorkflow(emailId: string): Promise<WorkflowResponse> {
  const data = await request<WorkflowResponse>(`/emails/${emailId}/workflow`);
  // Convert snake_case to camelCase for history items
  return {
    ...data,
    history: data.history.map((item) => ({
      ...item,
      triggeredBy: (item as unknown as { triggered_by: string }).triggered_by,
    })),
  };
}

/**
 * 转换工作流状态
 * @param emailId 邮件 ID
 * @param newState 新状态
 * @param triggeredBy 触发者
 * @param reason 原因
 * @param metadata 元数据
 */
export async function transitionWorkflowState(
  emailId: string,
  newState: string,
  triggeredBy: string,
  reason?: string,
  metadata?: Record<string, unknown>
): Promise<{ workflow: WorkflowResponse; message: string }> {
  return request<{ workflow: WorkflowResponse; message: string }>(
    `/emails/${emailId}/workflow/transition`,
    {
      method: 'POST',
      body: JSON.stringify({
        new_state: newState,
        triggered_by: triggeredBy,
        reason,
        metadata,
      }),
    }
  );
}

/**
 * 检查是否需要审批
 * @param emailId 邮件 ID
 * @param amount 金额
 * @param threshold 审批阈值
 */
export async function checkApprovalRequired(
  emailId: string,
  amount: number,
  threshold: number = 10000
): Promise<{ requires_approval: boolean; reason: string; next_state: string }> {
  const params = new URLSearchParams({
    amount: amount.toString(),
    threshold: threshold.toString(),
  });
  return request(`/emails/${emailId}/workflow/check-approval?${params}`);
}
