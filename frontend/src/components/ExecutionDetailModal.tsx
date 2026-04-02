/**
 * Agent 执行详情弹窗组件
 * 展示单个 Agent 执行的详细信息
 */
import React, { useCallback } from 'react';
import { useExecutionDetail } from '../hooks/monitoring';
import type { ExecutionDetail, ExecutionStep } from '../types/monitoring';

interface ExecutionDetailModalProps {
  taskId: string | null;
  onClose: () => void;
}

export const ExecutionDetailModal: React.FC<ExecutionDetailModalProps> = ({ taskId, onClose }) => {
  const { data: detail, isLoading, error } = useExecutionDetail(taskId);

  const handleBackdropClick = useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }, [onClose]);

  // 按 ESC 关闭
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  if (!taskId) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fade-in"
      onClick={handleBackdropClick}
    >
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] w-full max-w-4xl max-h-[90vh] overflow-hidden shadow-[0_20px_60px_rgba(0,0,0,0.6)] animate-scale-in m-4">
        {/* Header */}
        <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-6 py-4 border-b border-[#475569] flex items-center justify-between">
          <h2 className="text-xl font-semibold text-[#e2e8f0]">🔍 执行详情 | Execution Details</h2>
          <button
            onClick={onClose}
            className="text-[#94a3b8] hover:text-[#e2e8f0] transition-colors text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
          {isLoading ? (
            <DetailSkeleton />
          ) : error ? (
            <div className="p-6 text-center text-[#ef4444]">
              <div className="text-2xl mb-2">❌</div>
              <div>加载失败：{error.message}</div>
            </div>
          ) : detail ? (
            <ExecutionDetailContent detail={detail} />
          ) : (
            <div className="p-6 text-center text-[#94a3b8]">
              <div className="text-2xl mb-2">📭</div>
              <div>无执行数据 | No Execution Data</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

interface ExecutionDetailContentProps {
  detail: ExecutionDetail;
}

const ExecutionDetailContent: React.FC<ExecutionDetailContentProps> = ({ detail }) => {
  const getStatusClass = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-[rgba(16,185,129,0.2)] text-[#10b981]';
      case 'running': return 'bg-[rgba(245,158,11,0.2)] text-[#f59e0b]';
      case 'failed': return 'bg-[rgba(239,68,68,0.2)] text-[#ef4444]';
      default: return 'bg-[rgba(100,116,139,0.2)] text-[#94a3b8]';
    }
  };

  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="p-6 space-y-6">
      {/* 基本信息 */}
      <div className="bg-[rgba(15,23,42,0.5)] rounded-xl border border-[#334155] p-4">
        <h3 className="text-sm font-medium text-[#f97316] mb-3">📋 基本信息 | Basic Information</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-[#64748b]">任务 ID | Task ID</span>
            <div className="text-[#e2e8f0] font-mono mt-1">{detail.task_id}</div>
          </div>
          <div>
            <span className="text-[#64748b]">Agent 名称 | Agent Name</span>
            <div className="text-[#e2e8f0] font-mono mt-1">{detail.agent_name}</div>
          </div>
          <div>
            <span className="text-[#64748b]">状态 | Status</span>
            <div className={`inline-block px-2 py-1 rounded text-xs font-medium mt-1 ${getStatusClass(detail.status)}`}>
              {detail.status.toUpperCase()}
            </div>
          </div>
          <div>
            <span className="text-[#64748b]">邮件 ID</span>
            <div className="text-[#e2e8f0] font-mono mt-1">{detail.email_id}</div>
          </div>
          <div>
            <span className="text-[#64748b]">开始时间</span>
            <div className="text-[#e2e8f0] mt-1">{formatTime(detail.started_at)}</div>
          </div>
          <div>
            <span className="text-[#64748b]">完成时间</span>
            <div className="text-[#e2e8f0] mt-1">{formatTime(detail.completed_at)}</div>
          </div>
          <div>
            <span className="text-[#64748b]">分配预算</span>
            <div className="text-[#e2e8f0] font-mono mt-1">${detail.budget_allocated.toFixed(4)}</div>
          </div>
          <div>
            <span className="text-[#64748b]">实际成本</span>
            <div className="text-[#e2e8f0] font-mono mt-1">${detail.actual_cost.toFixed(4)}</div>
          </div>
        </div>
      </div>

      {/* 邮件信息 */}
      {(detail.email_subject || detail.email_from) && (
        <div className="bg-[rgba(15,23,42,0.5)] rounded-xl border border-[#334155] p-4">
          <h3 className="text-sm font-medium text-[#f97316] mb-3">📧 邮件信息 | Email Information</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            {detail.email_subject && (
              <div className="col-span-2">
                <span className="text-[#64748b]">主题 | Subject</span>
                <div className="text-[#e2e8f0] mt-1">{detail.email_subject}</div>
              </div>
            )}
            {detail.email_from && (
              <div>
                <span className="text-[#64748b]">发件人 | From</span>
                <div className="text-[#e2e8f0] mt-1">{detail.email_from}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 执行步骤 */}
      {detail.execution_steps && detail.execution_steps.length > 0 && (
        <div className="bg-[rgba(15,23,42,0.5)] rounded-xl border border-[#334155] p-4">
          <h3 className="text-sm font-medium text-[#f97316] mb-3">📝 执行步骤 | Execution Steps</h3>
          <div className="space-y-3">
            {detail.execution_steps.map((step, index) => (
              <ExecutionStepItem key={index} step={step} index={index + 1} />
            ))}
          </div>
        </div>
      )}

      {/* 错误信息 */}
      {detail.error_message && (
        <div className="bg-[rgba(239,68,68,0.1)] rounded-xl border border-[#ef4444] p-4">
          <h3 className="text-sm font-medium text-[#ef4444] mb-2">⚠️ 错误信息 | Error Message</h3>
          <div className="text-[#e2e8f0] text-sm font-mono bg-[#0f172a] rounded p-3 overflow-x-auto">
            {detail.error_message}
          </div>
        </div>
      )}

      {/* 结果摘要 */}
      {detail.result_summary && (
        <div className="bg-[rgba(16,185,129,0.1)] rounded-xl border border-[#10b981] p-4">
          <h3 className="text-sm font-medium text-[#10b981] mb-2">✓ 结果摘要 | Result Summary</h3>
          <div className="text-[#e2e8f0] text-sm">{detail.result_summary}</div>
        </div>
      )}
    </div>
  );
};

interface ExecutionStepItemProps {
  step: ExecutionStep;
  index: number;
}

const ExecutionStepItem: React.FC<ExecutionStepItemProps> = ({ step, index }) => {
  const getStatusClass = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-[rgba(16,185,129,0.2)] text-[#10b981] border-[#10b981]';
      case 'running': return 'bg-[rgba(245,158,11,0.2)] text-[#f59e0b] border-[#f59e0b] animate-pulse';
      case 'failed': return 'bg-[rgba(239,68,68,0.2)] text-[#ef4444] border-[#ef4444]';
      default: return 'bg-[rgba(100,116,139,0.2)] text-[#94a3b8] border-[#94a3b8]';
    }
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="bg-[#0f172a] rounded-lg border border-[#334155] p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-[#64748b]">#{index}</span>
          <span className="text-sm font-medium text-[#e2e8f0]">{step.step_name}</span>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded border ${getStatusClass(step.status)}`}>
          {step.status.toUpperCase()}
        </span>
      </div>
      <div className="grid grid-cols-4 gap-2 text-xs">
        <div>
          <span className="text-[#64748b]">开始时间</span>
          <div className="text-[#e2e8f0] font-mono">{formatTime(step.started_at)}</div>
        </div>
        <div>
          <span className="text-[#64748b]">耗时</span>
          <div className="text-[#e2e8f0] font-mono">{formatDuration(step.duration_ms)}</div>
        </div>
        <div>
          <span className="text-[#64748b]">成本</span>
          <div className="text-[#e2e8f0] font-mono">${step.cost.toFixed(4)}</div>
        </div>
        <div>
          <span className="text-[#64748b]">模型</span>
          <div className="text-[#e2e8f0] font-mono">{step.model_used || '-'}</div>
        </div>
      </div>
      {step.tokens_used && (
        <div className="mt-2 text-xs text-[#64748b]">
          Tokens: <span className="text-[#e2e8f0] font-mono">输入 {step.tokens_used.input} / 输出 {step.tokens_used.output}</span>
        </div>
      )}
    </div>
  );
};

// 骨架屏组件
const DetailSkeleton: React.FC = () => (
  <div className="p-6 space-y-4 animate-pulse">
    <div className="bg-[rgba(15,23,42,0.5)] rounded-xl border border-[#334155] p-4">
      <div className="h-4 bg-[#334155] rounded w-32 mb-3" />
      <div className="grid grid-cols-2 gap-4">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div key={i}>
            <div className="h-3 bg-[#334155] rounded w-20 mb-1" />
            <div className="h-4 bg-[#334155] rounded w-24" />
          </div>
        ))}
      </div>
    </div>
    <div className="bg-[rgba(15,23,42,0.5)] rounded-xl border border-[#334155] p-4">
      <div className="h-4 bg-[#334155] rounded w-24 mb-3" />
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-[#334155] rounded" />
        ))}
      </div>
    </div>
  </div>
);

export default ExecutionDetailModal;
