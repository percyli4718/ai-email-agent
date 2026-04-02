/**
 * 审批详情组件
 *
 * 功能:
 * - 显示审批请求的完整信息
 * - 显示关联邮件信息
 * - 提供批准/拒绝操作
 * - 显示审批历史
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { API_BASE_URL } from '../types/api';

// ============================================================================
// Types
// ============================================================================

export interface ApprovalDetailProps {
  approvalId: number;
  onBack?: () => void;
  onApproved?: (id: number) => void;
  onRejected?: (id: number) => void;
}

export interface ApprovalRequest {
  id: number;
  email_id: string;
  requester: string;
  request_type: string;
  amount: number | null;
  currency: string;
  reason: string;
  details?: Record<string, any> | null;
  status: 'pending' | 'approved' | 'rejected' | 'cancelled';
  reviewer?: string | null;
  reviewed_at?: string | null;
  comments?: string | null;
  created_at: string;
  email?: {
    id: string;
    subject: string;
    from_address: string;
    company?: string;
    product_name?: string;
  };
}

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

const getRequestTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    high_amount: '高金额审批 | High Amount',
    special_terms: '特殊条款审批 | Special Terms',
    new_customer: '新客户审批 | New Customer',
    risk_control: '风控审批 | Risk Control',
    other: '其他审批 | Other',
  };
  return labels[type] || type;
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
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// ============================================================================
// Detail Section Component
// ============================================================================

interface DetailSectionProps {
  title: string;
  icon: string;
  children: React.ReactNode;
}

const DetailSection: React.FC<DetailSectionProps> = ({ title, icon, children }) => (
  <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-xl border border-[#334155] p-5">
    <h3 className="text-sm font-semibold text-[#e2e8f0] mb-4 flex items-center gap-2">
      <span className="text-lg">{icon}</span>
      {title}
    </h3>
    {children}
  </div>
);

interface DetailRowProps {
  label: string;
  value: string | React.ReactNode;
}

const DetailRow: React.FC<DetailRowProps> = ({ label, value }) => (
  <div className="flex items-start justify-between py-2 border-b border-[#334155] last:border-0">
    <span className="text-xs text-[#94a3b8]">{label}</span>
    <span className="text-sm text-[#e2e8f0] text-right">{value}</span>
  </div>
);

// ============================================================================
// Main Component
// ============================================================================

const ApprovalDetail: React.FC<ApprovalDetailProps> = ({
  approvalId,
  onBack,
  onApproved,
  onRejected,
}) => {
  const queryClient = useQueryClient();
  const [comments, setComments] = useState('');
  const [showComments, setShowComments] = useState(false);

  // Fetch approval details
  const { data: approval, isLoading, error } = useQuery<ApprovalRequest>({
    queryKey: ['approval', approvalId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/approvals/${approvalId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch approval details');
      }
      return response.json();
    },
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${API_BASE_URL}/approvals/${approvalId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewer: 'current_user',
          comments: comments || undefined,
        }),
      });
      if (!response.ok) {
        throw new Error('Failed to approve request');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      queryClient.invalidateQueries({ queryKey: ['approval', approvalId] });
      onApproved?.(approvalId);
      setShowComments(false);
      setComments('');
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${API_BASE_URL}/approvals/${approvalId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewer: 'current_user',
          comments: comments || 'No comments provided',
        }),
      });
      if (!response.ok) {
        throw new Error('Failed to reject request');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      queryClient.invalidateQueries({ queryKey: ['approval', approvalId] });
      onRejected?.(approvalId);
      setShowComments(false);
      setComments('');
    },
  });

  const handleApprove = () => {
    if (comments.trim()) {
      approveMutation.mutate();
    } else {
      setShowComments(true);
    }
  };

  const handleReject = () => {
    if (comments.trim()) {
      rejectMutation.mutate();
    } else {
      setShowComments(true);
    }
  };

  const handleActionWithComments = (action: 'approve' | 'reject') => {
    if (action === 'approve') {
      approveMutation.mutate();
    } else {
      rejectMutation.mutate();
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-[#334155] rounded w-1/3"></div>
          <div className="h-32 bg-[#334155] rounded"></div>
          <div className="h-32 bg-[#334155] rounded"></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !approval) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-xl border border-[#334155] p-8 text-center">
        <div className="text-4xl mb-4">❌</div>
        <div className="text-[#ef4444] text-lg font-medium mb-2">加载失败 | Load Failed</div>
        <div className="text-[#94a3b8] text-sm">{error?.message || '审批请求不存在'}</div>
        {onBack && (
          <button
            onClick={onBack}
            className="mt-4 px-4 py-2 text-sm font-medium text-[#3b82f6] hover:text-[#60a5fa] border border-[#3b82f6] rounded-lg"
          >
            ← 返回列表 | Back to List
          </button>
        )}
      </div>
    );
  }

  const statusClass = getStatusClass(approval.status);
  const typeIcon = getRequestTypeIcon(approval.request_type);
  const typeLabel = getRequestTypeLabel(approval.request_type);
  const statusLabel = getStatusLabel(approval.status);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="text-[#94a3b8] hover:text-[#e2e8f0] transition-colors"
            >
              ← 返回 | Back
            </button>
          )}
          <div className="flex items-center gap-3">
            <span className="text-3xl">{typeIcon}</span>
            <div>
              <h2 className="text-xl font-bold text-[#e2e8f0]">{typeLabel}</h2>
              <p className="text-xs text-[#94a3b8]">ID: #{approval.id}</p>
            </div>
          </div>
        </div>
        <span className={`px-4 py-2 rounded-full text-sm font-medium border ${statusClass}`}>
          {statusLabel}
        </span>
      </div>

      {/* Amount Display */}
      {approval.amount && (
        <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-xl border border-[#334155] p-6 text-center">
          <div className="text-sm text-[#94a3b8] mb-2">审批金额 | Approval Amount</div>
          <div className="text-4xl font-bold text-[#60a5fa] font-mono">
            {formatCurrency(approval.amount, approval.currency)}
          </div>
        </div>
      )}

      {/* Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Request Info */}
        <DetailSection title="请求信息 | Request Info" icon="📄">
          <DetailRow label="申请人 | Requester" value={approval.requester} />
          <DetailRow label="审批类型 | Request Type" value={approval.request_type} />
          <DetailRow label="币种 | Currency" value={approval.currency} />
          <DetailRow
            label="创建时间 | Created"
            value={formatDate(approval.created_at)}
          />
        </DetailSection>

        {/* Email Info */}
        <DetailSection title="关联邮件 | Related Email" icon="📧">
          {approval.email ? (
            <>
              <DetailRow label="邮件主题 | Subject" value={approval.email.subject} />
              <DetailRow label="发件人 | From" value={approval.email.from_address} />
              {approval.email.company && (
                <DetailRow label="公司 | Company" value={approval.email.company} />
              )}
              {approval.email.product_name && (
                <DetailRow label="产品 | Product" value={approval.email.product_name} />
              )}
            </>
          ) : (
            <div className="text-sm text-[#94a3b8]">邮件信息不可用 | Email info not available</div>
          )}
        </DetailSection>
      </div>

      {/* Reason */}
      <DetailSection title="申请原因 | Reason" icon="💡">
        <p className="text-sm text-[#e2e8f0] whitespace-pre-wrap">{approval.reason}</p>
      </DetailSection>

      {/* Details JSON */}
      {approval.details && Object.keys(approval.details).length > 0 && (
        <DetailSection title="详细信息 | Details" icon="📊">
          <pre className="text-xs text-[#94a3b8] bg-[#0f172a] p-4 rounded-lg overflow-x-auto">
            {JSON.stringify(approval.details, null, 2)}
          </pre>
        </DetailSection>
      )}

      {/* Reviewer Info */}
      {approval.reviewer && (
        <DetailSection title="审批信息 | Review Info" icon="✍️">
          <DetailRow label="审批人 | Reviewer" value={approval.reviewer} />
          <DetailRow label="审批时间 | Reviewed At" value={approval.reviewed_at ? formatDate(approval.reviewed_at) : '-'} />
          {approval.comments && (
            <div className="mt-3 pt-3 border-t border-[#334155]">
              <div className="text-xs text-[#94a3b8] mb-1">审批意见 | Comments</div>
              <p className="text-sm text-[#e2e8f0]">{approval.comments}</p>
            </div>
          )}
        </DetailSection>
      )}

      {/* Action Buttons */}
      {approval.status === 'pending' && (
        <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-xl border border-[#334155] p-6">
          <h3 className="text-sm font-semibold text-[#e2e8f0] mb-4">审批操作 | Approval Actions</h3>

          {/* Comments Input */}
          {showComments && (
            <div className="mb-4">
              <label className="block text-xs text-[#94a3b8] mb-2">
                审批意见 | Comments (可选 | Optional)
              </label>
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="请输入审批意见..."
                className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-[#e2e8f0] focus:border-[#60a5fa] focus:outline-none resize-none"
                rows={3}
              />
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => showComments ? handleActionWithComments('reject') : handleReject()}
              disabled={rejectMutation.isPending}
              className="flex-1 px-4 py-3 text-sm font-medium rounded-lg bg-[rgba(239,68,68,0.2)] text-[#ef4444] border border-[#ef4444] hover:bg-[rgba(239,68,68,0.3)] transition-colors disabled:opacity-50"
            >
              {rejectMutation.isPending ? '处理中...' : '✕ 拒绝 | Reject'}
            </button>
            <button
              onClick={() => showComments ? handleActionWithComments('approve') : handleApprove()}
              disabled={approveMutation.isPending}
              className="flex-1 px-4 py-3 text-sm font-medium rounded-lg bg-[rgba(16,185,129,0.2)] text-[#10b981] border border-[#10b981] hover:bg-[rgba(16,185,129,0.3)] transition-colors disabled:opacity-50"
            >
              {approveMutation.isPending ? '处理中...' : '✓ 批准 | Approve'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApprovalDetail;
