/**
 * Agent 监控 API 服务
 */
import type { AgentExecution, AgentMetrics, CostStats, TrendDataPoint, ExecutionDetail } from '../types/monitoring';

const API_BASE_URL = '/api';

/**
 * 获取 Agent 执行历史记录
 */
export async function getAgentExecutions(limit: number = 50): Promise<AgentExecution[]> {
  const response = await fetch(`${API_BASE_URL}/agents/executions?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch agent executions: ${response.status}`);
  }
  return response.json();
}

/**
 * 获取单个 Agent 执行详情
 */
export async function getExecutionDetail(taskId: string): Promise<ExecutionDetail> {
  const response = await fetch(`${API_BASE_URL}/agents/executions/${taskId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch execution detail: ${response.status}`);
  }
  return response.json();
}

/**
 * 获取 Agent 性能指标
 */
export async function getAgentMetrics(): Promise<AgentMetrics[]> {
  const response = await fetch(`${API_BASE_URL}/agents/metrics`);
  if (!response.ok) {
    throw new Error(`Failed to fetch agent metrics: ${response.status}`);
  }
  return response.json();
}

/**
 * 获取成本统计数据
 */
export async function getCostStats(days: number = 30): Promise<CostStats[]> {
  const response = await fetch(`${API_BASE_URL}/metrics/cost-stats?days=${days}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch cost stats: ${response.status}`);
  }
  return response.json();
}

/**
 * 获取成本趋势数据
 */
export async function getCostTrend(days: number = 30): Promise<TrendDataPoint[]> {
  const response = await fetch(`${API_BASE_URL}/metrics/cost-trend?days=${days}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch cost trend: ${response.status}`);
  }
  return response.json();
}

/**
 * 获取性能趋势数据
 */
export async function getPerformanceTrend(days: number = 30): Promise<TrendDataPoint[]> {
  const response = await fetch(`${API_BASE_URL}/metrics/performance-trend?days=${days}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch performance trend: ${response.status}`);
  }
  return response.json();
}

/**
 * 获取监控仪表板汇总数据
 */
export async function getMonitoringDashboard(): Promise<{
  summary: {
    totalExecutions: number;
    successRate: number;
    totalCostToday: number;
    avgCostPerEmail: number;
    avgProcessingTimeMs: number;
    activeAgents: number;
  };
  recentExecutions: AgentExecution[];
  costTrend: TrendDataPoint[];
  performanceTrend: TrendDataPoint[];
}> {
  const response = await fetch(`${API_BASE_URL}/metrics/dashboard`);
  if (!response.ok) {
    throw new Error(`Failed to fetch monitoring dashboard: ${response.status}`);
  }
  return response.json();
}
