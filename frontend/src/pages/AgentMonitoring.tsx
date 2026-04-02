/**
 * Agent 监控系统页面
 * 展示 Agent 执行历史、性能指标和成本统计
 */
import React, { useState } from 'react';
import { useAgentExecutions, useMonitoringDashboard } from '../hooks/monitoring';
import { AgentMetrics } from '../components/AgentMetrics';
import { CostDashboard } from '../components/CostDashboard';
import { ExecutionDetailModal } from '../components/ExecutionDetailModal';
import type { AgentExecution } from '../types/monitoring';

const AgentMonitoring: React.FC = () => {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const limit = 50; // 默认显示 50 条记录

  const { data: executions, isLoading, error } = useAgentExecutions(limit);
  const { data: dashboard } = useMonitoringDashboard();

  // 过滤执行记录
  const filteredExecutions = statusFilter !== 'all'
    ? executions?.filter((ex) => ex.status === statusFilter)
    : executions;

  // 计算汇总数据
  const summary = dashboard?.summary || {
    totalExecutions: executions?.length || 0,
    successRate: 0,
    totalCostToday: 0,
    avgCostPerEmail: 0,
    avgProcessingTimeMs: 0,
    activeAgents: 0,
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-[#e2e8f0]">🤖 Agent 监控 | Agent Monitoring</h2>
        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#1e293b] border border-[#334155] text-[#e2e8f0] text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-[#60a5fa]"
          >
            <option value="all">全部状态 | All</option>
            <option value="pending">等待中 | Pending</option>
            <option value="running">运行中 | Running</option>
            <option value="completed">已完成 | Completed</option>
            <option value="failed">失败 | Failed</option>
          </select>
        </div>
      </div>

      {/* 汇总卡片 */}
      <SummaryCards summary={summary} />

      {/* Agent 性能指标 */}
      <AgentMetrics onAgentClick={(agentName) => console.log('Agent clicked:', agentName)} />

      {/* 成本趋势图表 */}
      <CostDashboard days={30} />

      {/* 执行历史记录 */}
      <ExecutionHistory
        executions={filteredExecutions || []}
        isLoading={isLoading}
        error={error}
        onExecutionClick={setSelectedTaskId}
      />

      {/* 执行详情弹窗 */}
      <ExecutionDetailModal
        taskId={selectedTaskId}
        onClose={() => setSelectedTaskId(null)}
      />
    </div>
  );
};

// 汇总卡片组件
interface SummaryCardsProps {
  summary: {
    totalExecutions: number;
    successRate: number;
    totalCostToday: number;
    avgCostPerEmail: number;
    avgProcessingTimeMs: number;
    activeAgents: number;
  };
}

const SummaryCards: React.FC<SummaryCardsProps> = ({ summary }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    <SummaryCard
      title="总执行数 | Total Executions"
      value={summary.totalExecutions.toString()}
      icon="📊"
      trend="+12 今天"
      trendUp={true}
    />
    <SummaryCard
      title="成功率 | Success Rate"
      value={`${(summary.successRate * 100).toFixed(1)}%`}
      icon="✓"
      trend="+2.3% 改进"
      trendUp={summary.successRate >= 0.95}
    />
    <SummaryCard
      title="今日成本 | Today's Cost"
      value={`$${summary.totalCostToday.toFixed(2)}`}
      icon="💰"
      trend="-5% vs 昨日"
      trendUp={true}
    />
    <SummaryCard
      title="活跃 Agent | Active Agents"
      value={summary.activeAgents.toString()}
      icon="🤖"
      trend="运行中"
      trendUp={true}
    />
  </div>
);

interface SummaryCardProps {
  title: string;
  value: string | number;
  icon: string;
  trend: string;
  trendUp: boolean;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ title, value, icon, trend, trendUp }) => (
  <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] p-5 shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm text-[#94a3b8]">{title}</span>
      <span className="text-xl">{icon}</span>
    </div>
    <div className="text-xl font-bold text-[#e2e8f0] mb-1">{value}</div>
    <div className={`text-xs ${trendUp ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>{trend}</div>
  </div>
);

// 执行历史记录组件
interface ExecutionHistoryProps {
  executions: AgentExecution[];
  isLoading: boolean;
  error: Error | null;
  onExecutionClick: (taskId: string) => void;
}

const ExecutionHistory: React.FC<ExecutionHistoryProps> = ({
  executions,
  isLoading,
  error,
  onExecutionClick,
}) => {
  const getStatusClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-[rgba(16,185,129,0.2)] text-[#10b981]';
      case 'running':
        return 'bg-[rgba(245,158,11,0.2)] text-[#f59e0b] animate-pulse';
      case 'failed':
        return 'bg-[rgba(239,68,68,0.2)] text-[#ef4444]';
      default:
        return 'bg-[rgba(100,116,139,0.2)] text-[#94a3b8]';
    }
  };

  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDuration = (start: string | null, end: string | null) => {
    if (!start || !end) return '-';
    const duration = new Date(end).getTime() - new Date(start).getTime();
    if (duration < 1000) return `${duration.toFixed(0)}ms`;
    return `${(duration / 1000).toFixed(1)}s`;
  };

  if (isLoading) {
    return <ExecutionHistorySkeleton />;
  }

  if (error) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] p-6">
        <div className="text-center text-[#ef4444]">
          <div className="text-2xl mb-2">❌</div>
          <div>加载执行历史失败：{error.message}</div>
        </div>
      </div>
    );
  }

  if (!executions || executions.length === 0) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] p-6">
        <div className="text-center text-[#94a3b8]">
          <div className="text-2xl mb-2">📭</div>
          <div>暂无执行记录 | No Execution History</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
      <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569] flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[#e2e8f0]">📜 执行历史 | Execution History</h2>
        <span className="text-sm text-[#94a3b8]">{executions.length} 条记录</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-[#0f172a]">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-[#94a3b8] uppercase tracking-wider">
                任务 ID | Task ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-[#94a3b8] uppercase tracking-wider">
                Agent
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-[#94a3b8] uppercase tracking-wider">
                状态 | Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-[#94a3b8] uppercase tracking-wider">
                邮件 | Email
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-[#94a3b8] uppercase tracking-wider">
                开始时间 | Started
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-[#94a3b8] uppercase tracking-wider">
                耗时 | Duration
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-[#94a3b8] uppercase tracking-wider">
                成本 | Cost
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e293b]">
            {executions.map((execution, index) => (
              <tr
                key={execution.task_id}
                onClick={() => onExecutionClick(execution.task_id)}
                className="hover:bg-[rgba(96,165,250,0.1)] cursor-pointer transition-colors animate-fade-in"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <td className="px-4 py-3 text-sm font-mono text-[#60a5fa]">
                  #{execution.task_id.slice(-6)}
                </td>
                <td className="px-4 py-3 text-sm text-[#e2e8f0]">
                  {execution.agent_name.replace('_agent', '')}
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusClass(execution.status)}`}>
                    {execution.status.toUpperCase()}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-[#94a3b8]">
                  {execution.email_id.slice(-8)}
                </td>
                <td className="px-4 py-3 text-sm text-[#94a3b8]">
                  {formatTime(execution.started_at)}
                </td>
                <td className="px-4 py-3 text-sm text-[#e2e8f0] font-mono">
                  {formatDuration(execution.started_at, execution.completed_at)}
                </td>
                <td className="px-4 py-3 text-sm text-[#e2e8f0] font-mono text-right">
                  ${execution.actual_cost.toFixed(4)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// 骨架屏组件
const ExecutionHistorySkeleton: React.FC = () => (
  <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.4)] animate-pulse">
    <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
      <div className="h-5 bg-[#334155] rounded w-48" />
    </div>
    <div className="p-4 space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex gap-4">
          {[1, 2, 3, 4, 5, 6, 7].map((j) => (
            <div key={j} className="h-8 bg-[#334155] rounded flex-1" />
          ))}
        </div>
      ))}
    </div>
  </div>
);

export default AgentMonitoring;
