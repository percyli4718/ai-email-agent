/**
 * Workflow Timeline Component
 *
 * 功能:
 * - 可视化邮件处理工作流状态
 * - 显示状态变更历史时间线
 * - 高亮当前状态
 * - 显示审批状态和原因
 *
 * 状态机流转:
 *   pending → processing → awaiting_approval → approved → completed
 *                                   ↓                    ↓
 *                               rejected            failed/cancelled
 */
import React from 'react';

// ============================================================================
// Types
// ============================================================================

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

export interface Workflow {
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

export interface WorkflowTimelineProps {
  workflow: Workflow | null;
  loading?: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const STATE_CONFIG: Record<string, { label: string; icon: string; color: string; description: string }> = {
  pending: {
    label: '待处理',
    icon: '⏳',
    color: 'bg-gray-100 border-gray-300 text-gray-600',
    description: '等待处理'
  },
  processing: {
    label: '处理中',
    icon: '🔄',
    color: 'bg-blue-50 border-blue-300 text-blue-600',
    description: '正在处理'
  },
  awaiting_approval: {
    label: '待审批',
    icon: '📋',
    color: 'bg-amber-50 border-amber-300 text-amber-600',
    description: '等待审批'
  },
  approved: {
    label: '已批准',
    icon: '✅',
    color: 'bg-green-50 border-green-300 text-green-600',
    description: '已批准'
  },
  rejected: {
    label: '已拒绝',
    icon: '❌',
    color: 'bg-red-50 border-red-300 text-red-600',
    description: '已拒绝'
  },
  completed: {
    label: '已完成',
    icon: '✨',
    color: 'bg-emerald-50 border-emerald-300 text-emerald-600',
    description: '已完成'
  },
  failed: {
    label: '失败',
    icon: '⚠️',
    color: 'bg-orange-50 border-orange-300 text-orange-600',
    description: '处理失败'
  },
  cancelled: {
    label: '已取消',
    icon: '🚫',
    color: 'bg-gray-50 border-gray-300 text-gray-400',
    description: '已取消'
  }
};

const TRIGGERED_BY_LABELS: Record<string, string> = {
  system: '系统',
  agent: '智能代理',
  user: '用户',
  approval_rule: '审批规则'
};

// ============================================================================
// Helper Functions
// ============================================================================

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getStateConfig = (state: string) => {
  return STATE_CONFIG[state] || {
    label: state,
    icon: '❓',
    color: 'bg-gray-50 border-gray-300 text-gray-600',
    description: 'Unknown state'
  };
};

const getTriggeredByLabel = (triggeredBy: string): string => {
  return TRIGGERED_BY_LABELS[triggeredBy] || triggeredBy;
};

// ============================================================================
// Components
// ============================================================================

/**
 * 状态节点组件
 */
const StateNode: React.FC<{
  state: string;
  isCurrent: boolean;
  isPast: boolean;
  index: number;
}> = ({ state, isCurrent, isPast, index }) => {
  const config = getStateConfig(state);

  return (
    <div className="flex items-center">
      {/* 节点圆圈 */}
      <div
        data-testid={`state-node-${state}`}
        className={`
          relative z-10 flex items-center justify-center
          w-10 h-10 rounded-full border-2 transition-all duration-300
          ${isCurrent
            ? `${config.color} border-current scale-110 shadow-lg`
            : isPast
              ? 'bg-gray-200 border-gray-300 text-gray-500'
              : 'bg-white border-gray-300 text-gray-400'
          }
        `}
        title={config.description}
      >
        <span className="text-lg">{config.icon}</span>

        {/* 状态标签 */}
        {isCurrent && (
          <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
            <span className={`text-xs font-semibold ${config.color.split(' ')[2]}`}>
              {config.label}
            </span>
          </div>
        )}
      </div>

      {/* 连接线 */}
      {index < 3 && (
        <div
          className={`
            flex-1 h-0.5 mx-2 transition-all duration-300
            ${isPast ? 'bg-gray-300' : 'bg-gray-200'}
          `}
        />
      )}
    </div>
  );
};

/**
 * 历史记录项组件
 */
const HistoryItem: React.FC<{
  item: WorkflowHistoryItem;
  isFirst: boolean;
}> = ({ item, isFirst }) => {
  const config = getStateConfig(item.to_state);

  return (
    <div data-testid="workflow-history-item" className={`flex gap-3 ${isFirst ? '' : 'mt-3'}`}>
      {/* 时间线点 */}
      <div className="flex flex-col items-center">
        <div
          className={`
            w-3 h-3 rounded-full
            ${config.color.split(' ')[0]} ${config.color.split(' ')[2]}
          `}
        />
        {!isFirst && <div className="w-0.5 flex-1 bg-gray-200 my-1" />}
      </div>

      {/* 内容卡片 */}
      <div
        className={`
          flex-1 p-3 rounded-lg border bg-white
          ${isFirst ? 'border-blue-200 shadow-md' : 'border-gray-200'}
        `}
      >
        <div className="flex items-center justify-between mb-1">
          <span className={`text-sm font-semibold ${config.color.split(' ')[2]}`}>
            {config.label}
          </span>
          <span className="text-xs text-gray-500">
            {formatDate(item.created_at)}
          </span>
        </div>

        <div className="text-xs text-gray-600 mb-1">
          <span className="font-medium">触发者：</span>{' '}
          {getTriggeredByLabel(item.triggeredBy)}
        </div>

        {item.reason && (
          <div className="text-xs text-gray-500 italic bg-gray-50 p-2 rounded">
            {item.reason}
          </div>
        )}

        {item.metadata && Object.keys(item.metadata).length > 0 && (
          <details className="mt-2">
            <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600">
              元数据
            </summary>
            <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-auto max-h-32">
              {JSON.stringify(item.metadata, null, 2)}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
};

/**
 * 审批提示组件
 */
const ApprovalBadge: React.FC<{
  requiresApproval: boolean;
  reason: string | null;
  amount: number | null;
}> = ({ requiresApproval, reason, amount }) => {
  if (!requiresApproval) return null;

  return (
    <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">📋</span>
        <span className="font-semibold text-amber-800">
          需要审批
        </span>
      </div>
      {reason && (
        <p className="text-sm text-amber-700">{reason}</p>
      )}
      {amount && (
        <p className="text-sm text-amber-700 mt-1">
          金额：${amount.toLocaleString()}
        </p>
      )}
    </div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

/**
 * 工作流时间线组件
 *
 * 展示邮件处理的完整流程，包括:
 * - 当前状态可视化
 * - 状态流转历史
 * - 审批状态提示
 */
export const WorkflowTimeline: React.FC<WorkflowTimelineProps> = ({
  workflow,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="p-6 text-center text-gray-500">
        <div className="animate-pulse">加载中...</div>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="p-6 text-center text-gray-400">
        <div className="text-2xl mb-2">📭</div>
        <div>无工作流记录</div>
      </div>
    );
  }

  // 定义状态流转顺序
  const stateOrder = ['pending', 'processing', 'awaiting_approval', 'approved', 'completed'];
  const currentStateIndex = stateOrder.indexOf(workflow.current_state);

  // 渲染状态流转图
  const renderStateFlow = () => {
    return (
      <div className="flex items-center justify-between mb-6 p-4 bg-gray-50 rounded-xl">
        {stateOrder.map((state, index) => (
          <StateNode
            key={state}
            state={state}
            isCurrent={workflow.current_state === state}
            isPast={index < currentStateIndex}
            index={index}
          />
        ))}
      </div>
    );
  };

  // 渲染历史记录
  const renderHistory = () => {
    if (!workflow.history || workflow.history.length === 0) {
      return (
        <div className="text-center text-gray-400 py-4">
          暂无历史记录
        </div>
      );
    }

    return (
      <div className="mt-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <span>📜</span>
          流程历史
        </h3>
        <div className="space-y-1">
          {workflow.history.slice().reverse().map((item, index) => (
            <HistoryItem
              key={item.id}
              item={item}
              isFirst={index === workflow.history.length - 1}
            />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div data-testid="workflow-timeline" className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* 头部 */}
      <div className="px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200">
        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          <span>🔄</span>
          处理流程
        </h2>
        <p className="text-xs text-gray-500 mt-1">
          邮件 ID: {workflow.email_id}
        </p>
      </div>

      {/* 内容 */}
      <div className="p-4">
        {/* 状态流转图 */}
        {renderStateFlow()}

        {/* 审批提示 */}
        <ApprovalBadge
          requiresApproval={workflow.requires_approval}
          reason={workflow.approval_reason}
          amount={workflow.approval_amount}
        />

        {/* 历史记录 */}
        {renderHistory()}

        {/* 时间戳 */}
        <div className="mt-4 pt-3 border-t border-gray-100 flex justify-between text-xs text-gray-400">
          <span>
            创建于：{formatDate(workflow.created_at)}
          </span>
          <span>
            更新于：{formatDate(workflow.updated_at)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default WorkflowTimeline;
