/**
 * 审批列表页面
 *
 * 功能:
 * - 显示待处理/已批准/已拒绝的审批列表
 * - 支持按状态过滤
 * - 支持点击查看详情
 * - 支持批准/拒绝操作
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { API_BASE_URL } from '../types/api';
import type { ApprovalRequest } from '../types/approval';
import ApprovalDetail from '../components/ApprovalDetail';

// ============================================================================
// Types
// ============================================================================

interface ApprovalsResponse {
  requests: ApprovalRequest[];
  total: number;
}

type FilterStatus = 'all' | 'pending' | 'approved' | 'rejected';

// ============================================================================
// Helper Functions
// ============================================================================

const getRequestTypeIcon = (type: string): string => {
  const icons: Record<string, string> = {
    high_amount: '💰',
    special_terms: '📋',
    new_customer: '👤',
    risk_control: '⚠️',
    other: '📝',
  };
  return icons[type] || '📝';
};

const getStatusClass = (status: string): string => {
  const classes: Record<string, string> = {
    pending: 'bg-[rgba(245,158,11,0.2)] text-[#f59e0b] border-[#f59e0b]',
    approved: 'bg-[rgba(16,185,129,0.2)] text-[#10b981] border-[#10b981]',
    rejected: 'bg-[rgba(239,68,68,0.2)] text-[#ef4444] border-[#ef4444]',
    cancelled: 'bg-[rgba(100,116,139,0.2)] text-[#94a3b8] border-[#94a3b8]',
  };
  return classes[status] || classes.pending;
};

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: '待处理 | Pending',
    approved: '已批准 | Approved',
    rejected: '已拒绝 | Rejected',
    cancelled: '已取消 | Cancelled',
  };
  return labels[status] || status;
};

const formatCurrency = (amount: number | null, currency: string): string => {
  if (amount === null || amount === undefined) return '-';
  const symbols: Record<string, string> = {
    USD: '$',
    EUR: '€',
    BRL: 'R$',
    CNY: '¥',
  };
  const symbol = symbols[currency] || currency;
  return `${symbol}${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// ============================================================================
// Approval Card Component (inline for simplicity)
// ============================================================================

interface ApprovalCardProps {
  approval: ApprovalRequest;
  onClick: (id: number) => void;
  onApprove: (id: number) => void;
  onReject: (id: number) => void;
}

const ApprovalCard: React.FC<ApprovalCardProps> = ({
  approval,
  onClick,
  onApprove,
  onReject,
}) => {
  const statusClass = getStatusClass(approval.status);
  const statusLabel = getStatusLabel(approval.status);
  const typeIcon = getRequestTypeIcon(approval.request_type);

  return (
    <div
      className={`p-4 rounded-xl border transition-all cursor-pointer ${
        approval.status === 'pending'
          ? 'bg-gradient-to-br from-[#1e293b] to-[#0f172a] border-[#334155] hover:border-[#60a5fa]'
          : 'bg-[#0f172a] border-[#1e293b] opacity-80'
      }`}
      onClick={() => onClick(approval.id)}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-start gap-3 flex-1">
          <span className="text-2xl">{typeIcon}</span>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-[#e2e8f0] truncate">
              {approval.request_type}
            </h3>
            <p className="text-xs text-[#94a3b8] mt-0.5 truncate">
              申请人 | Requester: {approval.requester}
            </p>
          </div>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${statusClass}`}>
          {statusLabel}
        </span>
      </div>

      {/* Amount */}
      {approval.amount && (
        <div className="mb-3">
          <div className="text-2xl font-bold text-[#60a5fa] font-mono">
            {formatCurrency(approval.amount, approval.currency)}
          </div>
        </div>
      )}

      {/* Reason Preview */}
      <p className="text-xs text-[#94a3b8] line-clamp-2 mb-3">
        {approval.reason}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-[#64748b]">
        <span>ID: #{approval.id}</span>
        <span>{formatDate(approval.created_at)}</span>
      </div>

      {/* Action Buttons for Pending */}
      {approval.status === 'pending' && (
        <div className="flex gap-2 mt-4 pt-3 border-t border-[#334155]" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => onReject(approval.id)}
            className="flex-1 px-3 py-2 text-xs font-medium rounded-lg bg-[rgba(239,68,68,0.2)] text-[#ef4444] border border-[#ef4444] hover:bg-[rgba(239,68,68,0.3)] transition-colors"
          >
            ✕ 拒绝 | Reject
          </button>
          <button
            onClick={() => onApprove(approval.id)}
            className="flex-1 px-3 py-2 text-xs font-medium rounded-lg bg-[rgba(16,185,129,0.2)] text-[#10b981] border border-[#10b981] hover:bg-[rgba(16,185,129,0.3)] transition-colors"
          >
            ✓ 批准 | Approve
          </button>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

export interface ApprovalsProps {
  selectedApprovalId?: number | null;
  onApprovalViewed?: () => void;
}

const Approvals: React.FC<ApprovalsProps> = ({
  selectedApprovalId: propSelectedApprovalId = null,
  onApprovalViewed,
}) => {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<FilterStatus>('all');
  const [internalSelectedApprovalId, setInternalSelectedApprovalId] = useState<number | null>(null);

  // Use prop value if provided, otherwise use internal state
  const selectedApprovalId = propSelectedApprovalId !== null ? propSelectedApprovalId : internalSelectedApprovalId;

  const setSelectedApprovalId = (id: number | null) => {
    setInternalSelectedApprovalId(id);
    if (id === null && onApprovalViewed) {
      onApprovalViewed();
    }
  };

  const [comments, setComments] = useState<Record<number, string>>({});

  // Fetch approvals list
  const { data, isLoading, error } = useQuery<ApprovalsResponse>({
    queryKey: ['approvals', filter],
    queryFn: async () => {
      const params = filter !== 'all' ? `?status=${filter}` : '';
      const response = await fetch(`${API_BASE_URL}/approvals${params}`);
      if (!response.ok) {
        throw new Error('Failed to fetch approvals');
      }
      return response.json();
    },
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: async (id: number) => {
      const response = await fetch(`${API_BASE_URL}/approvals/${id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewer: 'current_user',
          comments: comments[id] || undefined,
        }),
      });
      if (!response.ok) {
        throw new Error('Failed to approve');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      if (selectedApprovalId) {
        queryClient.invalidateQueries({ queryKey: ['approval', selectedApprovalId] });
      }
      setComments({});
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: async (id: number) => {
      const response = await fetch(`${API_BASE_URL}/approvals/${id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewer: 'current_user',
          comments: comments[id] || 'No comments provided',
        }),
      });
      if (!response.ok) {
        throw new Error('Failed to reject');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      if (selectedApprovalId) {
        queryClient.invalidateQueries({ queryKey: ['approval', selectedApprovalId] });
      }
      setComments({});
    },
  });

  const handleApprove = (id: number) => {
    approveMutation.mutate(id);
  };

  const handleReject = (id: number) => {
    rejectMutation.mutate(id);
  };

  const handleCardClick = (id: number) => {
    setSelectedApprovalId(id);
  };

  const handleBack = () => {
    setSelectedApprovalId(null);
  };

  // Filter tabs
  const tabs: { key: FilterStatus; label: string; count?: number }[] = [
    { key: 'all', label: '全部 | All' },
    { key: 'pending', label: '待处理 | Pending' },
    { key: 'approved', label: '已批准 | Approved' },
    { key: 'rejected', label: '已拒绝 | Rejected' },
  ];

  // Show detail view
  if (selectedApprovalId) {
    return (
      <div>
        <ApprovalDetail
          approvalId={selectedApprovalId}
          onBack={handleBack}
          onApproved={() => {
            queryClient.invalidateQueries({ queryKey: ['approvals'] });
            setSelectedApprovalId(null);
          }}
          onRejected={() => {
            queryClient.invalidateQueries({ queryKey: ['approvals'] });
            setSelectedApprovalId(null);
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-[#e2e8f0]">✅ 审批中心 | Approvals</h2>
      </div>

      {/* Filter Tabs */}
      <div className="flex border-b border-[#334155]">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              filter === tab.key
                ? 'text-[#3b82f6] border-b-2 border-[#3b82f6] bg-[rgba(59,130,246,0.1)]'
                : 'text-[#94a3b8] hover:text-[#e2e8f0]'
            }`}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span className="ml-2 text-xs">({tab.count})</span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-40 bg-[#334155] rounded-xl"></div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-xl border border-[#334155] p-8 text-center">
          <div className="text-4xl mb-4">❌</div>
          <div className="text-[#ef4444] text-lg font-medium mb-2">加载失败 | Load Failed</div>
          <div className="text-[#94a3b8] text-sm">{error.message}</div>
        </div>
      ) : !data?.requests || data.requests.length === 0 ? (
        <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-xl border border-[#334155] p-8 text-center">
          <div className="text-4xl mb-4">📭</div>
          <div className="text-[#e2e8f0] text-lg font-medium mb-2">暂无审批 | No Approvals</div>
          <div className="text-[#94a3b8] text-sm">
            {filter === 'all' ? '暂无审批请求' : `暂无${filter}状态的审批`}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.requests.map((approval) => (
            <ApprovalCard
              key={approval.id}
              approval={approval}
              onClick={handleCardClick}
              onApprove={handleApprove}
              onReject={handleReject}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Approvals;
