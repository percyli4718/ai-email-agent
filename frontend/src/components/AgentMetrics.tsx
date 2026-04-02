/**
 * Agent 性能指标组件
 * 展示各 Agent 的执行统计和性能指标
 */
import React from 'react';
import { useAgentMetrics } from '../hooks/monitoring';
import type { AgentMetrics as AgentMetricsType } from '../types/monitoring';

interface AgentMetricsProps {
  onAgentClick?: (agentName: string) => void;
}

export const AgentMetrics: React.FC<AgentMetricsProps> = ({ onAgentClick }) => {
  const { data: metrics, isLoading, error } = useAgentMetrics();

  if (isLoading) {
    return <AgentMetricsSkeleton />;
  }

  if (error) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] p-6">
        <div className="text-center text-[#ef4444]">
          <div className="text-2xl mb-2">❌</div>
          <div>加载性能指标失败 | Load Metrics Failed: {error.message}</div>
        </div>
      </div>
    );
  }

  if (!metrics || metrics.length === 0) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] p-6">
        <div className="text-center text-[#94a3b8]">
          <div className="text-2xl mb-2">📭</div>
          <div>暂无性能数据 | No Metrics Data</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
      <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
        <h2 className="text-lg font-semibold text-[#e2e8f0]">📊 Agent 性能指标 | Agent Performance Metrics</h2>
      </div>
      <div className="p-5">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.map((agent, index) => (
            <AgentMetricCard
              key={agent.agent_name}
              agent={agent}
              delay={index * 100}
              onClick={() => onAgentClick?.(agent.agent_name)}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

const AgentMetricCard: React.FC<AgentMetricCardProps> = ({ agent, delay, onClick }) => {
  const getStatusColor = (successRate: number) => {
    if (successRate >= 0.95) return 'text-[#10b981]';
    if (successRate >= 0.80) return 'text-[#f59e0b]';
    return 'text-[#ef4444]';
  };

  const formatNumber = (num: number, decimals: number = 2) => {
    return num.toFixed(decimals);
  };

  return (
    <div
      className="bg-[rgba(15,23,42,0.8)] rounded-xl border border-[#334155] p-4 hover:border-[#60a5fa] transition-all cursor-pointer animate-fade-in"
      style={{ animationDelay: `${delay}ms` }}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-[#f97316]">{agent.agent_name.replace('_agent', '')}</span>
        <span className={`text-xs font-mono ${getStatusColor(agent.success_rate)}`}>
          {(agent.success_rate * 100).toFixed(0)}% 成功率
        </span>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-[#64748b]">执行次数</span>
          <span className="text-[#e2e8f0] font-mono">{agent.total_executions}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-[#64748b]">成功/失败</span>
          <span className="text-[#e2e8f0] font-mono">
            <span className="text-[#10b981]">{agent.successful_executions}</span>
            {' / '}
            <span className="text-[#ef4444]">{agent.failed_executions}</span>
          </span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-[#64748b]">平均耗时</span>
          <span className="text-[#e2e8f0] font-mono">{(agent.avg_execution_time_ms / 1000).toFixed(1)}s</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-[#64748b]">平均成本</span>
          <span className="text-[#e2e8f0] font-mono">${formatNumber(agent.avg_cost, 4)}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-[#64748b]">总成本</span>
          <span className="text-[#e2e8f0] font-mono">${formatNumber(agent.total_cost, 2)}</span>
        </div>
      </div>
    </div>
  );
};

interface AgentMetricCardProps {
  agent: AgentMetricsType;
  delay?: number;
  onClick?: () => void;
}

// 骨架屏组件
const AgentMetricsSkeleton: React.FC = () => (
  <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
    <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
      <h2 className="text-lg font-semibold text-[#e2e8f0]">📊 Agent 性能指标 | Agent Performance Metrics</h2>
    </div>
    <div className="p-5">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-[rgba(15,23,42,0.8)] rounded-xl border border-[#334155] p-4 animate-pulse">
            <div className="flex items-center justify-between mb-3">
              <div className="h-4 bg-[#334155] rounded w-20" />
              <div className="h-3 bg-[#334155] rounded w-12" />
            </div>
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map((j) => (
                <div key={j} className="flex justify-between">
                  <div className="h-3 bg-[#334155] rounded w-16" />
                  <div className="h-3 bg-[#334155] rounded w-12" />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default AgentMetrics;
