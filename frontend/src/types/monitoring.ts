/**
 * Agent 监控系统类型定义
 */

// Agent 执行历史记录项
export interface AgentExecution {
  id: string;
  task_id: string;
  email_id: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  budget_allocated: number;
  actual_cost: number;
  started_at: string | null;
  completed_at: string | null;
  error_message?: string | null;
  result_summary?: string | null;
}

// Agent 性能指标
export interface AgentMetrics {
  agent_name: string;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  avg_execution_time_ms: number;
  avg_cost: number;
  total_cost: number;
  success_rate: number;
}

// 成本统计项
export interface CostStats {
  date: string;
  total_cost: number;
  avg_cost_per_email: number;
  email_count: number;
  sonnet_cost: number;
  haiku_cost: number;
}

// 趋势数据点
export interface TrendDataPoint {
  date: string;
  cost: number;
  emails: number;
  avgTime?: number;
}

// Agent 执行详情
export interface ExecutionDetail extends AgentExecution {
  email_subject?: string;
  email_from?: string;
  execution_steps?: ExecutionStep[];
}

// 执行步骤
export interface ExecutionStep {
  step_name: string;
  started_at: string;
  completed_at: string;
  duration_ms: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  cost: number;
  model_used?: string;
  tokens_used?: {
    input: number;
    output: number;
  };
}

// 监控仪表板数据
export interface MonitoringDashboard {
  summary: SummaryMetrics;
  recentExecutions: AgentExecution[];
  costTrend: TrendDataPoint[];
  performanceTrend: TrendDataPoint[];
}

// 汇总指标
export interface SummaryMetrics {
  totalExecutions: number;
  successRate: number;
  totalCostToday: number;
  avgCostPerEmail: number;
  avgProcessingTimeMs: number;
  activeAgents: number;
}
