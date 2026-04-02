import React, { useState, useCallback } from 'react';
import { useEmails } from './hooks/useEmails';
import { useEmailAnalysis } from './hooks/useEmailAnalysis';
import { useMetrics, useTraces, usePromptVersions, usePrometheusMetrics } from './hooks';
import { useAgentsStatus } from './hooks/useAgentsStatus';
import { Email as ApiEmail, AnalysisSection, Metric, TraceSpan, PromptVersion, Agent } from './types/api';
import GenerateEmailPanel from './components/GenerateEmailPanel';
import TemplateEditor from './components/TemplateEditor';
import NotificationCenter, { type Notification } from './components/NotificationCenter';
import Approvals from './pages/Approvals';
import type { GeneratedEmail } from './types/generator';

// ============================================================================
// Types
// ============================================================================

interface PrometheusMetrics {
  counters: Record<string, number>;
  gauges: Record<string, number>;
  histograms: Record<string, {
    count: number;
    sum: number;
    avg: number;
    min: number;
    max: number;
    p50: number;
    p95: number;
  }>;
}

// ============================================================================
// 类型定义
// ============================================================================

/** 子 Agent 状态（扩展 API Agent 类型） */
export interface SubAgentStatus extends Agent {
  icon?: string;
}

/** CEO Agent 状态 */
export interface CEOAgentStatus {
  name: string;
  status: 'Running' | 'Completed' | 'Pending';
  budgetUsed: number;
  budgetMax: number;
  taskId?: string;
  subAgents: SubAgentStatus[];
}

/** Layer 执行日志条目 */
interface LayerLogEntry {
  icon: string;
  name: string;
  description: string;
  time: string;
  layerType: 'layer1' | 'layer2' | 'layer3' | 'agent';
  status: 'pending' | 'running' | 'completed' | 'error';
}

// 当前任务 ID（实际应用中可能从路由或上下文获取）
const CURRENT_TRACE_ID = '2847';

// ============================================================================
// 主组件
// ============================================================================

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'inbox' | 'agents' | 'metrics' | 'templates' | 'approvals'>('inbox');
  const [selectedEmail, setSelectedEmail] = useState<string | null>(null);
  const [selectedApprovalId, setSelectedApprovalId] = useState<number | null>(null);

  // Get refetch from useEmails hook
  const { refetch } = useEmails();

  // Handle new emails generated
  const handleNewEmailsGenerated = useCallback((emails: GeneratedEmail[]) => {
    console.log('新邮件已生成:', emails);
    // Trigger refresh of email list
    refetch();
  }, [refetch]);

  // Handle notification click
  const handleNotificationClick = useCallback((notification: Notification) => {
    if (notification.type === 'approval_request' && notification.related_id) {
      const approvalId = parseInt(notification.related_id, 10);
      if (!isNaN(approvalId)) {
        setSelectedApprovalId(approvalId);
        setActiveTab('approvals');
      }
    }
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-[#e2e8f0]">
      {/* Header */}
      <header className="bg-[#1e293b] border-b border-[#334155]">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-[#60a5fa]">📧 AI Email Agent · 智能邮件代理</h1>
              <p className="text-sm text-[#94a3b8] mt-1">医药分销自动化系统 | Pharmaceutical Distribution</p>
            </div>
            <div className="flex items-center gap-4">
              <NotificationCenter onNotificationClick={handleNotificationClick} />
              <div className="text-right">
                <div className="text-xs text-[#64748b]">系统状态 | System Status</div>
                <div className="text-sm text-[#10b981] font-medium">● 全部运行正常 | All Systems Operational</div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-[#1e293b] border-b border-[#334155]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex space-x-1">
            <TabButton
              active={activeTab === 'inbox'}
              onClick={() => setActiveTab('inbox')}
              label="📨 收件箱 | Inbox"
              activeColor="text-[#60a5fa] border-[#60a5fa]"
            />
            <TabButton
              active={activeTab === 'agents'}
              onClick={() => setActiveTab('agents')}
              label="🤖 Agent 监控 | Agents"
              activeColor="text-[#f97316] border-[#f97316]"
            />
            <TabButton
              active={activeTab === 'metrics'}
              onClick={() => setActiveTab('metrics')}
              label="📊 指标 | Metrics"
              activeColor="text-[#a855f7] border-[#a855f7]"
            />
            <TabButton
              active={activeTab === 'templates'}
              onClick={() => setActiveTab('templates')}
              label="📝 模板管理 | Templates"
              activeColor="text-[#10b981] border-[#10b981]"
            />
            <TabButton
              active={activeTab === 'approvals'}
              onClick={() => setActiveTab('approvals')}
              label="✅ 审批 | Approvals"
              activeColor="text-[#ec4899] border-[#ec4899]"
            />
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {activeTab === 'inbox' && (
          <div>
            <div className="mb-4 flex justify-between items-center">
              <h2 className="text-xl font-bold text-[#e2e8f0]">📨 收件箱 | Inbox</h2>
              <GenerateEmailPanel onEmailsGenerated={handleNewEmailsGenerated} />
            </div>
            <InboxTab
              selectedEmail={selectedEmail}
              onSelectEmail={setSelectedEmail}
            />
          </div>
        )}
        {activeTab === 'agents' && <AgentsTab />}
        {activeTab === 'metrics' && <MetricsTab />}
        {activeTab === 'templates' && <TemplateEditor onTemplateUpdated={() => {}} />}
        {activeTab === 'approvals' && (
          <Approvals
            selectedApprovalId={selectedApprovalId}
            onApprovalViewed={() => setSelectedApprovalId(null)}
          />
        )}
      </main>
    </div>
  );
};

// ============================================================================
// Tab Button Component
// ============================================================================

interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  label: string;
  activeColor: string;
}

const TabButton: React.FC<TabButtonProps> = ({ active, onClick, label, activeColor }) => (
  <button
    onClick={onClick}
    className={`px-5 py-3 text-sm font-medium transition-all ${
      active
        ? `${activeColor} border-b-2`
        : 'text-[#94a3b8] hover:text-[#e2e8f0]'
    }`}
  >
    {label}
  </button>
);

// ============================================================================
// Inbox Tab Component
// ============================================================================

interface InboxTabProps {
  selectedEmail: string | null;
  onSelectEmail: (id: string | null) => void;
}

const InboxTab: React.FC<InboxTabProps> = ({ selectedEmail, onSelectEmail }) => {
  // 使用 useEmailAnalysis hook 获取选中邮件的分析数据
  const { data: analysisSections, isLoading, error } = useEmailAnalysis(selectedEmail);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Email List */}
      <EmailList
        selectedEmail={selectedEmail}
        onSelectEmail={onSelectEmail}
      />

      {/* AI Analysis Panel */}
      <div className="space-y-4">
        {selectedEmail ? (
          isLoading ? (
            <AnalysisSkeleton />
          ) : error ? (
            <ErrorState message={error.message} />
          ) : analysisSections && analysisSections.length > 0 ? (
            analysisSections.map((section, index) => (
              <AnalysisPanel
                key={index}
                section={section}
                delay={index * 100}
              />
            ))
          ) : (
            <EmptyState message="暂无分析数据" />
          )
        ) : (
          <EmptyState />
        )}
      </div>
    </div>
  );
};

// ============================================================================
// Email List Component
// ============================================================================

interface EmailListProps {
  selectedEmail: string | null;
  onSelectEmail: (id: string | null) => void;
}

const EmailList: React.FC<EmailListProps> = ({ selectedEmail, onSelectEmail }) => {
  // 使用 useEmails hook 获取邮件列表
  const { data: emails, isLoading, error } = useEmails();

  const getStatusClass = (status: ApiEmail['status']) => {
    switch (status) {
      case 'new': return 'bg-[#10b981] shadow-[0_0_10px_#10b981]';
      case 'processing': return 'bg-[#f59e0b] shadow-[0_0_10px_#f59e0b]';
      case 'done': return 'bg-[#64748b]';
    }
  };

  const getPriorityClass = (priority: ApiEmail['priority']) => {
    switch (priority) {
      case 'high': return 'bg-[rgba(239,68,68,0.2)] text-[#ef4444]';
      case 'medium': return 'bg-[rgba(245,158,11,0.2)] text-[#f59e0b]';
      case 'low': return 'bg-[rgba(100,116,139,0.2)] text-[#94a3b8]';
    }
  };

  // Loading 状态 - 骨架屏
  if (isLoading) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
        <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
          <h2 className="text-lg font-semibold text-[#e2e8f0]">收件箱 - 未处理邮件 | Inbox - Unprocessed Emails</h2>
        </div>
        <div>
          {[1, 2, 3].map((i) => (
            <div key={i} className="px-5 py-4 border-b border-[#1e293b] animate-pulse">
              <div className="flex items-start gap-4">
                <div className="w-2.5 h-2.5 rounded-full mt-1.5 bg-[#334155]" />
                <div className="flex-1 min-w-0">
                  <div className="h-4 bg-[#334155] rounded w-3/4 mb-2" />
                  <div className="h-3 bg-[#334155] rounded w-full mb-2" />
                  <div className="flex gap-2">
                    <div className="h-4 bg-[#334155] rounded w-16" />
                    <div className="h-4 bg-[#334155] rounded w-12" />
                  </div>
                </div>
                <div className="text-right">
                  <div className="h-3 bg-[#334155] rounded w-16 mb-1" />
                  <div className="h-3 bg-[#334155] rounded w-20" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error 状态
  if (error) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
        <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
          <h2 className="text-lg font-semibold text-[#e2e8f0]">收件箱 - 未处理邮件 | Inbox - Unprocessed Emails</h2>
        </div>
        <div className="p-8 text-center">
          <div className="text-2xl mb-2">❌</div>
          <div className="text-[#ef4444]">加载失败 | Load Failed: {error.message}</div>
        </div>
      </div>
    );
  }

  // 空状态 - 无邮件
  if (!emails || emails.length === 0) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
        <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
          <h2 className="text-lg font-semibold text-[#e2e8f0]">收件箱 - 未处理邮件 | Inbox - Unprocessed Emails</h2>
        </div>
        <div className="p-8 text-center text-[#94a3b8]">
          <div className="text-4xl mb-3">📭</div>
          <div className="text-lg font-medium">收件箱为空 | Inbox Empty</div>
          <div className="text-sm mt-1">暂无待处理的邮件 | No pending emails</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
      <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
        <h2 className="text-lg font-semibold text-[#e2e8f0]">收件箱 - 未处理邮件 | Inbox - Unprocessed Emails</h2>
      </div>
      <div>
        {emails.map((email) => (
          <div
            key={email.id}
            onClick={() => onSelectEmail(email.id === selectedEmail ? null : email.id)}
            className={`px-5 py-4 border-b border-[#1e293b] transition-all cursor-pointer hover:bg-[rgba(96,165,250,0.1)] ${
              selectedEmail === email.id ? 'bg-[rgba(96,165,250,0.1)]' : ''
            }`}
          >
            <div className="flex items-start gap-4">
              {/* Status Indicator */}
              <div className={`w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0 ${getStatusClass(email.status)}`} />

              {/* Content */}
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-[#e2e8f0] truncate">{email.subject}</h3>
                <p className="text-sm text-[#94a3b8] mt-0.5 truncate">{email.preview}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${getPriorityClass(email.priority)}`}>
                    {email.priority.toUpperCase()}
                  </span>
                  <span className="text-[10px] text-[#64748b]">{email.region}</span>
                </div>
              </div>

              {/* Meta */}
              <div className="text-right flex-shrink-0">
                <div className="text-xs text-[#64748b]">{email.time}</div>
                <div className="text-xs text-[#64748b] mt-1">{email.from}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================================================
// Analysis Panel Component
// ============================================================================

interface AnalysisPanelProps {
  section: AnalysisSection;
  delay: number;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({ section, delay }) => (
  <div
    className="bg-[rgba(15,23,42,0.5)] rounded-xl border border-[#334155] p-4 animate-fade-in"
    style={{ animationDelay: `${delay}ms` }}
  >
    <div className="flex items-center justify-between mb-3">
      <span className="text-sm font-semibold text-[#60a5fa]">{section.title}</span>
      <span className="text-[10px] bg-[rgba(96,165,250,0.2)] text-[#60a5fa] px-2 py-0.5 rounded">
        {section.badge}
      </span>
    </div>
    <div className="grid grid-cols-2 gap-2.5">
      {section.fields.map((field, index) => (
        <div
          key={index}
          className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-2.5"
        >
          <div className="text-[10px] text-[#64748b] uppercase mb-1">
            {field.label}
          </div>
          <div className="text-sm text-[#e2e8f0] font-mono">
            {field.value}
          </div>
        </div>
      ))}
    </div>
  </div>
);

// ============================================================================
// Empty State Component
// ============================================================================

interface EmptyStateProps {
  message?: string;
}

const EmptyState: React.FC<EmptyStateProps> = ({ message }) => (
  <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] p-8 h-full flex items-center justify-center">
    <div className="text-center text-[#94a3b8]">
      <div className="text-4xl mb-3">👈</div>
      <div className="text-lg font-medium">{message || '选择一封邮件 | Select an email'}</div>
      {!message && (
        <div className="text-sm mt-1">查看 AI 分析结果和结构化输出 | View AI analysis</div>
      )}
    </div>
  </div>
);

// ============================================================================
// Analysis Skeleton Component (Loading 状态)
// ============================================================================

const AnalysisSkeleton: React.FC = () => (
  <>
    {[1, 2, 3].map((i) => (
      <div
        key={i}
        className="bg-[rgba(15,23,42,0.5)] rounded-xl border border-[#334155] p-4 animate-pulse"
      >
        <div className="flex items-center justify-between mb-3">
          <div className="h-4 bg-[#334155] rounded w-32" />
          <div className="h-4 bg-[#334155] rounded w-20" />
        </div>
        <div className="grid grid-cols-2 gap-2.5">
          {[1, 2, 3, 4].map((j) => (
            <div key={j} className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-2.5">
              <div className="h-2 bg-[#334155] rounded w-16 mb-2" />
              <div className="h-4 bg-[#334155] rounded w-full" />
            </div>
          ))}
        </div>
      </div>
    ))}
  </>
);

// ============================================================================
// Error State Component
// ============================================================================

interface ErrorStateProps {
  message: string;
}

const ErrorState: React.FC<ErrorStateProps> = ({ message }) => (
  <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] p-8 h-full flex items-center justify-center">
    <div className="text-center text-[#ef4444]">
      <div className="text-4xl mb-3">❌</div>
      <div className="text-lg font-medium">加载失败 | Load Failed</div>
      <div className="text-sm mt-1">{message}</div>
    </div>
  </div>
);

// ============================================================================
// Agents Tab Component
// ============================================================================

const AgentsTab: React.FC = () => {
  const { data: agents, isLoading, error } = useAgentsStatus();

  // Loading 状态
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="text-center text-[#94a3b8] py-12">
          <div className="text-2xl mb-2">⏳</div>
          <div>加载 Agent 状态中... | Loading Agent Status...</div>
        </div>
      </div>
    );
  }

  // Error 状态
  if (error) {
    return (
      <div className="space-y-6">
        <div className="text-center text-[#ef4444] py-12">
          <div className="text-2xl mb-2">❌</div>
          <div>加载失败 | Load Failed: {error.message}</div>
        </div>
      </div>
    );
  }

  // 无数据状态
  if (!agents || agents.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center text-[#94a3b8] py-12">
          <div className="text-2xl mb-2">📭</div>
          <div>暂无 Agent 数据 | No Agent Data</div>
        </div>
      </div>
    );
  }

  // 计算总预算
  const totalBudgetUsed = agents.reduce((sum, agent) => sum + agent.budget, 0);
  const totalBudgetMax = agents.reduce((sum, agent) => sum + agent.budgetMax, 0);
  const budgetPercentage = totalBudgetMax > 0 ? (totalBudgetUsed / totalBudgetMax) * 100 : 0;

  // 判断 CEO Agent 状态（只要有子 Agent 在 Running，整体就是 Running）
  const hasRunning = agents.some(a => a.status === 'Running');
  const hasPending = agents.some(a => a.status === 'Pending');
  const ceoStatus = hasRunning ? 'Running' : hasPending ? 'Pending' : 'Completed';

  return (
    <div className="space-y-6">
      {/* CEO Agent Card */}
      <CEOAgentCard
        status={ceoStatus}
        budgetUsed={totalBudgetUsed}
        budgetMax={totalBudgetMax}
        budgetPercentage={budgetPercentage}
        subAgents={agents}
        taskId={CURRENT_TRACE_ID}
      />

      {/* Layer Execution Log */}
      <LayerExecutionLog traceId={CURRENT_TRACE_ID} />
    </div>
  );
};

// ============================================================================
// CEO Agent Card Component
// ============================================================================

interface CEOAgentCardProps {
  status: 'Running' | 'Completed' | 'Pending';
  budgetUsed: number;
  budgetMax: number;
  budgetPercentage: number;
  subAgents: Agent[];
  taskId?: string;
}

const CEOAgentCard: React.FC<CEOAgentCardProps> = ({
  status,
  budgetUsed,
  budgetMax,
  budgetPercentage,
  subAgents,
  taskId
}) => {
  const getStatusColor = (s: string) => {
    switch (s) {
      case 'Running': return 'bg-[rgba(245,158,11,0.2)] text-[#f59e0b]';
      case 'Completed': return 'bg-[rgba(16,185,129,0.2)] text-[#10b981]';
      case 'Pending': return 'bg-[rgba(100,116,139,0.2)] text-[#94a3b8]';
    }
  };

  return (
    <div className="bg-[linear-gradient(145deg,rgba(249,115,22,0.1),rgba(15,23,42,0.5))] rounded-2xl border border-[rgba(249,115,22,0.3)] p-6">
      <div className="flex items-center justify-between mb-4">
        <span className="text-lg font-semibold text-[#f97316] flex items-center gap-2">
          📋 CEO Agent (任务分解器 | Task Decomposer)
        </span>
        <span className={`text-xs px-3 py-1 rounded-full font-medium ${getStatusColor(status)}`}>
          {status === 'Running' && '● '}
          {status === 'Completed' && '✓ '}
          {status === 'Pending' && '○ '}
          {status} {taskId && `· Task #${taskId}`}
        </span>
      </div>

      {/* Budget Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-[#94a3b8] mb-2">
          <span>预算消耗 | Budget Used</span>
          <span className="font-mono">${budgetUsed.toFixed(2)} / ${budgetMax.toFixed(2)}</span>
        </div>
        <div className="h-2 bg-[#0f172a] rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-[#f97316] to-[#fb923c] rounded-full transition-all duration-500"
            style={{ width: `${Math.min(budgetPercentage, 100)}%` }}
          />
        </div>
      </div>

      {/* Sub Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        {subAgents.map((agent, index) => (
          <SubAgentCard key={index} agent={agent} />
        ))}
      </div>
    </div>
  );
};

// ============================================================================
// Sub Agent Card Component
// ============================================================================

interface SubAgentCardProps {
  agent: Agent;
}

const SubAgentCard: React.FC<SubAgentCardProps> = ({ agent }) => {
  const getStatusStyle = (status: Agent['status']) => {
    switch (status) {
      case 'Running': return 'bg-[rgba(245,158,11,0.2)] text-[#f59e0b]';
      case 'Completed': return 'bg-[rgba(16,185,129,0.2)] text-[#10b981]';
      case 'Pending': return 'bg-[rgba(100,116,139,0.2)] text-[#94a3b8]';
    }
  };

  const getStatusIcon = (status: Agent['status']) => {
    switch (status) {
      case 'Running': return '●';
      case 'Completed': return '✓';
      case 'Pending': return '○';
    }
  };

  // 动态计算预算百分比
  const budgetPercentage = agent.budgetMax > 0 ? (agent.budget / agent.budgetMax) * 100 : 0;

  return (
    <div className="bg-[rgba(15,23,42,0.8)] rounded-xl border border-[#334155] p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-[#f97316]">{agent.name}</span>
        <span className={`text-[10px] px-2 py-0.5 rounded ${getStatusStyle(agent.status)}`}>
          {getStatusIcon(agent.status)}
        </span>
      </div>
      <div className="flex justify-between text-[10px] text-[#94a3b8] mb-1.5">
        <span>预算 | Budget</span>
        <span className="font-mono">${agent.budget.toFixed(2)}</span>
      </div>
      <div className="h-1.5 bg-[#0f172a] rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-[#f97316] to-[#fb923c] rounded-full"
          style={{ width: `${Math.min(budgetPercentage, 100)}%` }}
        />
      </div>
      {agent.description && (
        <div className="text-[10px] text-[#64748b] mt-2 truncate">
          {agent.description}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// Layer Execution Log Component
// ============================================================================

interface LayerExecutionLogProps {
  traceId: string;
}

const LayerExecutionLog: React.FC<LayerExecutionLogProps> = ({ traceId }) => {
  const { data: traces, isLoading, error } = useTraces(traceId);

  const getLayerBorderClass = (layerType: string) => {
    switch (layerType) {
      case 'layer1': return 'border-[#10b981]';
      case 'layer2': return 'border-[#a855f7]';
      case 'layer3': return 'border-[#f97316]';
      case 'agent': return 'border-[#f97316]';
      default: return 'border-[#64748b]';
    }
  };

  // 将 TraceSpan 映射到 Layer 条目
  const mapTracesToLayers = (spans: TraceSpan[]): LayerLogEntry[] => {
    return spans.map((span) => {
      const name = span.name.toLowerCase();
      let layerType: LayerLogEntry['layerType'] = 'agent';
      let icon = '📋';

      if (name.includes('layer 1') || name.includes('分类') || name.includes('路由')) {
        layerType = 'layer1';
        icon = '🔍';
      } else if (name.includes('layer 2') || name.includes('检索') || name.includes('chroma')) {
        layerType = 'layer2';
        icon = '🔗';
      } else if (name.includes('layer 3') || name.includes('生成') || name.includes('分析')) {
        layerType = 'layer3';
        icon = '📝';
      }

      return {
        icon,
        name: span.name,
        description: `耗时：${span.duration}`,
        time: span.time,
        layerType,
        status: 'completed'
      };
    });
  };

  // Loading 状态
  if (isLoading) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden">
        <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
          <h2 className="text-lg font-semibold text-[#e2e8f0]">🔬 邮件 #{traceId} - 完整执行日志 | Email #{traceId} - Full Execution Log</h2>
        </div>
        <div className="p-5 text-center text-[#94a3b8]">
          <div className="text-2xl mb-2">⏳</div>
          <div>加载执行日志中... | Loading Execution Log...</div>
        </div>
      </div>
    );
  }

  // Error 状态
  if (error) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden">
        <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
          <h2 className="text-lg font-semibold text-[#e2e8f0]">🔬 邮件 #{traceId} - 完整执行日志 | Email #{traceId} - Full Execution Log</h2>
        </div>
        <div className="p-5 text-center text-[#ef4444]">
          <div className="text-2xl mb-2">❌</div>
          <div>加载失败 | Load Failed: {error.message}</div>
        </div>
      </div>
    );
  }

  // 无数据状态
  if (!traces || traces.length === 0) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden">
        <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
          <h2 className="text-lg font-semibold text-[#e2e8f0]">🔬 邮件 #{traceId} - 完整执行日志 | Email #{traceId} - Full Execution Log</h2>
        </div>
        <div className="p-5 text-center text-[#94a3b8]">
          <div className="text-2xl mb-2">📭</div>
          <div>暂无执行日志 | No Execution Log</div>
        </div>
      </div>
    );
  }

  const layerLogs = mapTracesToLayers(traces);

  return (
    <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden">
      <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
        <h2 className="text-lg font-semibold text-[#e2e8f0]">🔬 邮件 #{traceId} - 完整执行日志 | Email #{traceId} - Full Execution Log</h2>
      </div>
      <div className="p-5">
        <div className="space-y-3">
          {layerLogs.map((layer, index) => (
            <div
              key={index}
              className={`flex items-center gap-4 p-3 bg-[#0f172a] rounded-xl border-l-4 ${getLayerBorderClass(layer.layerType)} animate-slide-in`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <span className="text-xl">{layer.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-[#e2e8f0]">{layer.name}</div>
                <div className="text-xs text-[#64748b] mt-0.5 font-mono">{layer.description}</div>
              </div>
              <span className="text-xs px-2.5 py-1 rounded font-mono bg-[rgba(16,185,129,0.2)] text-[#10b981]">
                ✓ {layer.time}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// Metrics Tab Component
// ============================================================================

const MetricsTab: React.FC = () => {
  const { data: metrics, isLoading: metricsLoading, error: metricsError } = useMetrics();
  const { data: traces, isLoading: tracesLoading, error: tracesError } = useTraces('current-trace');
  const { data: versions, isLoading: versionsLoading, error: versionsError } = usePromptVersions();
  const { data: prometheusData, isLoading: prometheusLoading } = usePrometheusMetrics();

  if (metricsLoading || tracesLoading || versionsLoading || prometheusLoading) {
    return (
      <div className="space-y-6">
        <div className="text-center text-[#94a3b8] py-12">
          <div className="text-2xl mb-2">⏳</div>
          <div>加载中 | Loading...</div>
        </div>
      </div>
    );
  }

  if (metricsError || tracesError || versionsError) {
    return (
      <div className="space-y-6">
        <div className="text-center text-[#ef4444] py-12">
          <div className="text-2xl mb-2">❌</div>
          <div>加载失败 | Load Failed: {(metricsError || tracesError || versionsError)?.message}</div>
        </div>
      </div>
    );
  }

  // 计算预算使用率
  const budgetSpent = prometheusData?.gauges['budget_spent'] || 0;
  const budgetMax = 0.50; // 默认 Agent 预算
  const budgetPercentage = Math.min((budgetSpent / budgetMax) * 100, 100);

  return (
    <div className="space-y-6">
      {/* Prometheus Metrics Section */}
      <PrometheusMetricsSection data={prometheusData} />

      {/* Budget Usage */}
      <BudgetUsageCard spent={budgetSpent} max={budgetMax} percentage={budgetPercentage} />

      {/* Standard Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {metrics?.map((metric, index) => (
          <MetricCard key={index} metric={metric} />
        ))}
      </div>

      {/* Trace Timeline & Prompt Evolution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TraceTimeline spans={traces || []} />
        <PromptEvolution versions={versions || []} />
      </div>
    </div>
  );
};

// ============================================================================
// Metric Card Component
// ============================================================================

interface MetricCardProps {
  metric: Metric;
}

const MetricCard: React.FC<MetricCardProps> = ({ metric }) => {
  // 格式化数值显示
  const formatValue = (value: string) => {
    // 百分比
    if (value.includes('%')) {
      return value;
    }
    // 美元
    if (value.startsWith('$')) {
      return value;
    }
    // 时间
    if (value.endsWith('ms') || value.endsWith('s')) {
      return value;
    }
    // 普通数字
    const num = parseFloat(value);
    if (!isNaN(num)) {
      if (num >= 1000) {
        return num.toLocaleString();
      }
      return value;
    }
    return value;
  };

  return (
    <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-xl border border-[#334155] p-5 text-center">
      <div className="text-3xl font-bold text-[#60a5fa] font-mono">{formatValue(metric.value)}</div>
      <div className="text-xs text-[#64748b] uppercase tracking-wide mt-2">{metric.name}</div>
      <div className={`text-xs mt-2 font-medium flex items-center justify-center gap-1 ${
        metric.trendUp !== false ? 'text-[#10b981]' : 'text-[#ef4444]'
      }`}>
        {metric.trendUp !== false ? '↑' : '↓'} {metric.trend.replace(/^[↑↓]\s*/, '')}
      </div>
    </div>
  );
};

// ============================================================================
// Trace Timeline Component
// ============================================================================

interface TraceTimelineProps {
  spans: TraceSpan[];
}

const TraceTimeline: React.FC<TraceTimelineProps> = ({ spans }) => {
  // 根据 span 名称获取颜色类别
  const getLayerColor = (name: string): string => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('layer 1') || lowerName.includes('分类')) {
      return 'from-[rgba(16,185,129,0.4)] to-[rgba(16,185,129,0.7)]'; // Green - Layer 1
    }
    if (lowerName.includes('layer 2') || lowerName.includes('检索') || lowerName.includes('chroma')) {
      return 'from-[rgba(168,85,247,0.4)] to-[rgba(168,85,247,0.7)]'; // Purple - Layer 2
    }
    if (lowerName.includes('layer 3') || lowerName.includes('生成') || lowerName.includes('分析')) {
      return 'from-[rgba(249,115,22,0.4)] to-[rgba(249,115,22,0.7)]'; // Orange - Layer 3
    }
    if (lowerName.includes('agent') || lowerName.includes('评审') || lowerName.includes('决策')) {
      return 'from-[rgba(59,130,246,0.4)] to-[rgba(59,130,246,0.7)]'; // Blue - Agent
    }
    return 'from-[rgba(34,197,94,0.4)] to-[rgba(34,197,94,0.7)]'; // Default - System
  };

  if (!spans || spans.length === 0) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden">
        <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
          <h2 className="text-lg font-semibold text-[#e2e8f0]">🔗 分布式追踪 (Trace)</h2>
        </div>
        <div className="p-5 text-center text-[#94a3b8]">
          <div>暂无追踪数据 | No Trace Data</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden">
      <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
        <h2 className="text-lg font-semibold text-[#e2e8f0]">🔗 分布式追踪 (Trace)</h2>
      </div>
      <div className="p-5">
        <div className="space-y-2">
          {spans.map((span, index) => (
            <div key={index} className="flex items-center gap-3">
              <span className="text-xs text-[#64748b] w-14 text-right font-mono">
                {span.time}
              </span>
              <div
                className={`flex-1 h-6 rounded-lg px-3 flex items-center text-sm text-[#e2e8f0] bg-gradient-to-r ${span.color || getLayerColor(span.name)}`}
              >
                <span className="truncate">{span.name}</span>
                <span className="ml-auto text-xs font-mono opacity-80">{span.duration}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// Prompt Evolution Component
// ============================================================================

interface PromptEvolutionProps {
  versions: PromptVersion[];
}

const PromptEvolution: React.FC<PromptEvolutionProps> = ({ versions }) => {
  if (!versions || versions.length === 0) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden">
        <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
          <h2 className="text-lg font-semibold text-[#e2e8f0]">🧬 Prompt 进化历史 (Autoresearch)</h2>
        </div>
        <div className="p-5 text-center text-[#94a3b8]">
          <div>暂无 Prompt 版本 | No Prompt Versions</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden">
      <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
        <h2 className="text-lg font-semibold text-[#e2e8f0]">🧬 Prompt 进化历史 (Autoresearch)</h2>
      </div>
      <div className="p-5">
        <div className="space-y-3">
          {versions.map((version, index) => (
            <div
              key={index}
              className="bg-[#0f172a] rounded-xl border border-[#334155] p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-mono text-[#a855f7]">{version.name}</span>
                <span className="text-xs bg-[rgba(168,85,247,0.2)] text-[#a855f7] px-2 py-0.5 rounded">
                  {version.score}
                </span>
              </div>
              <div className="space-y-1">
                {version.changes.map((change, changeIndex) => (
                  <div
                    key={changeIndex}
                    className={`text-xs font-mono ${
                      change.type === 'add' ? 'text-[#10b981]' : 'text-[#ef4444]'
                    }`}
                  >
                    {change.text}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default App;

// ============================================================================
// Prometheus Metrics Section Component
// ============================================================================

interface PrometheusMetricsSectionProps {
  data: PrometheusMetrics | null;
}

const PrometheusMetricsSection: React.FC<PrometheusMetricsSectionProps> = ({ data }) => {
  if (!data || (!Object.keys(data.counters).length && !Object.keys(data.gauges).length)) {
    return null;
  }

  return (
    <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden">
      <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
        <h2 className="text-lg font-semibold text-[#e2e8f0]">
          📊 Prometheus 指标 | Prometheus Metrics
        </h2>
      </div>
      <div className="p-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Counters */}
        {Object.entries(data.counters).map(([name, value]) => (
          <div key={name} className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-4">
            <div className="text-xs text-[#64748b] uppercase mb-1">{name}</div>
            <div className="text-xl font-bold text-[#10b981] font-mono">{value.toLocaleString()}</div>
            <div className="text-xs text-[#64748b] mt-1">Counter</div>
          </div>
        ))}
        {/* Gauges */}
        {Object.entries(data.gauges).map(([name, value]) => (
          <div key={name} className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-4">
            <div className="text-xs text-[#64748b] uppercase mb-1">{name}</div>
            <div className="text-xl font-bold text-[#f59e0b] font-mono">${value.toFixed(4)}</div>
            <div className="text-xs text-[#64748b] mt-1">Gauge</div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================================================
// Budget Usage Card Component
// ============================================================================

interface BudgetUsageCardProps {
  spent: number;
  max: number;
  percentage: number;
}

const BudgetUsageCard: React.FC<BudgetUsageCardProps> = ({ spent, max, percentage }) => {
  const getStatusColor = () => {
    if (percentage >= 90) return 'text-[#ef4444]';
    if (percentage >= 70) return 'text-[#f59e0b]';
    return 'text-[#10b981]';
  };

  const getBarColor = () => {
    if (percentage >= 90) return 'from-[#ef4444] to-[#dc2626]';
    if (percentage >= 70) return 'from-[#f59e0b] to-[#d97706]';
    return 'from-[#10b981] to-[#059669]';
  };

  return (
    <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden">
      <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[#e2e8f0]">
            💰 预算使用 | Budget Usage
          </h2>
          <span className={`text-sm font-medium ${getStatusColor()}`}>
            {percentage.toFixed(1)}%
          </span>
        </div>
      </div>
      <div className="p-5">
        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-[#94a3b8] mb-2">
            <span>已用 | Used: ${spent.toFixed(4)}</span>
            <span>预算 | Budget: ${max.toFixed(2)}</span>
          </div>
          <div className="h-3 bg-[#0f172a] rounded-full overflow-hidden">
            <div
              className={`h-full bg-gradient-to-r ${getBarColor()} rounded-full transition-all duration-500`}
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>

        {/* Budget Status */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-3 text-center">
            <div className="text-xs text-[#64748b] mb-1">剩余 | Remaining</div>
            <div className="text-lg font-bold text-[#10b981] font-mono">
              ${(max - spent).toFixed(4)}
            </div>
          </div>
          <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-3 text-center">
            <div className="text-xs text-[#64748b] mb-1">使用率 | Usage</div>
            <div className={`text-lg font-bold font-mono ${getStatusColor()}`}>
              {percentage.toFixed(1)}%
            </div>
          </div>
          <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-3 text-center">
            <div className="text-xs text-[#64748b] mb-1">状态 | Status</div>
            <div className={`text-lg font-bold ${getStatusColor()}`}>
              {percentage >= 90 ? '⚠️' : percentage >= 70 ? '⚡' : '✅'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
