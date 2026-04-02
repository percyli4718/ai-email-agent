/**
 * Agent 监控 React Query Hooks
 */
import { useQuery } from '@tanstack/react-query';
import {
  getAgentExecutions,
  getExecutionDetail,
  getAgentMetrics,
  getCostStats,
  getCostTrend,
  getPerformanceTrend,
  getMonitoringDashboard,
} from '../services/monitoring';
import type { AgentExecution, AgentMetrics, CostStats, TrendDataPoint, ExecutionDetail } from '../types/monitoring';

/**
 * 获取 Agent 执行历史记录
 */
export const useAgentExecutions = (limit: number = 50) => {
  return useQuery<AgentExecution[], Error>({
    queryKey: ['agent-executions', limit],
    queryFn: () => getAgentExecutions(limit),
    refetchInterval: 10000, // 10 秒轮询
  });
};

/**
 * 获取单个执行详情
 */
export const useExecutionDetail = (taskId: string | null) => {
  return useQuery<ExecutionDetail, Error>({
    queryKey: ['execution-detail', taskId],
    queryFn: () => getExecutionDetail(taskId!),
    enabled: !!taskId,
  });
};

/**
 * 获取 Agent 性能指标
 */
export const useAgentMetrics = () => {
  return useQuery<AgentMetrics[], Error>({
    queryKey: ['agent-metrics'],
    queryFn: getAgentMetrics,
    refetchInterval: 30000, // 30 秒轮询
  });
};

/**
 * 获取成本统计数据
 */
export const useCostStats = (days: number = 30) => {
  return useQuery<CostStats[], Error>({
    queryKey: ['cost-stats', days],
    queryFn: () => getCostStats(days),
  });
};

/**
 * 获取成本趋势数据
 */
export const useCostTrend = (days: number = 30) => {
  return useQuery<TrendDataPoint[], Error>({
    queryKey: ['cost-trend', days],
    queryFn: () => getCostTrend(days),
  });
};

/**
 * 获取性能趋势数据
 */
export const usePerformanceTrend = (days: number = 30) => {
  return useQuery<TrendDataPoint[], Error>({
    queryKey: ['performance-trend', days],
    queryFn: () => getPerformanceTrend(days),
  });
};

/**
 * 获取监控仪表板汇总数据
 */
export const useMonitoringDashboard = () => {
  return useQuery<{
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
  }, Error>({
    queryKey: ['monitoring-dashboard'],
    queryFn: getMonitoringDashboard,
    refetchInterval: 15000, // 15 秒轮询
  });
};
