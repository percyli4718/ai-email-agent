/**
 * 审批卡片组件
 *
 * 功能:
 * - 显示单个审批请求
 * - 提供批准/拒绝操作按钮
 * - 显示审批状态和详情
 */
import React, { useState } from 'react';
import type { ApprovalRequest } from '../types/approval';

// ============================================================================
// Types
// ============================================================================

export interface ApprovalCardProps {
  request: ApprovalRequest;
  onApprove: (id: number, comments?: string) => void;
  onReject: (id: number, comments: string) => void;
  onClick?: () => void;
}

// ============================================================================
// Helper Functions
// ============================================================================

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

const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    pending: 'bg-[#f59e0b] text-[#f59e0b]',
    approved: 'bg-[#10b981] text-[#10b981]',
    rejected: 'bg-[#ef4444] text-[#ef4444]',
    cancelled: 'bg-[#6b7280] text-[#6b7280]',
  };
  return colors[status] || colors.pending;
};

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: '待审批 | Pending',
    approved: '已批准 | Approved',
    rejected: '已拒绝 | Rejected',
    cancelled: '已取消 | Cancelled',
  };
  return labels[status] || status;
};

// ============================================================================
// ApprovalCard Component
// ============================================================================

export const ApprovalCard: React.FC<ApprovalCardProps> = ({
  request,
  onApprove,
  onReject,
  onClick,
}) => {
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const statusColor = getStatusColor(request.status);
  const typeLabel = getRequestTypeLabel(request.request_type);
  const statusLabel = getStatusLabel(request.status);

  const handleApprove = async () => {
    setIsProcessing(true);
    try {
      await onApprove(request.id, comments || undefined);
    } finally {
      setIsProcessing(false);
      setShowComments(false);
      setComments('');
    }
  };

  const handleReject = async () => {
    if (!comments.trim()) {
      alert('请输入拒绝原因 | Please enter rejection reason');
      return;
    }
    setIsProcessing(true);
    try {
      await onReject(request.id, comments);
    } finally {
      setIsProcessing(false);
      setShowComments(false);
      setComments('');
    }
  };

  const isPending = request.status === 'pending';

  return (
    <div
      className={`p-4 rounded-lg border transition-all cursor-pointer ${
        isPending
          ? 'bg-[#1e293b] border-[#334155] hover:border-[#3b82f6]'
          : 'bg-[#0f172a] border-[#1e293b] opacity-80'
      }`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">📋</span>
          <span className="text-sm font-medium text-[#e2e8f0]">
            审批请求 #{request.id}
          </span>
        </div>
        <span className={`px-2 py-1 rounded text-xs font-medium ${statusColor}`}>
          {statusLabel}
        </span>
      </div>

      {/* Type */}
      <div className="mb-2">
        <span className="text-xs text-[#64748b]">类型 | Type</span>
        <div className="text-sm text-[#e2e8f0]">{typeLabel}</div>
      </div>

      {/* Amount */}
      {request.amount && (
        <div className="mb-2">
          <span className="text-xs text-[#64748b]">金额 | Amount</span>
          <div className="text-sm text-[#e2e8f0]">
            {request.currency} {request.amount.toLocaleString()}
          </div>
        </div>
      )}

      {/* Reason */}
      <div className="mb-2">
        <span className="text-xs text-[#64748b]">原因 | Reason</span>
        <div className="text-sm text-[#94a3b8]">{request.reason}</div>
      </div>

      {/* Requester */}
      <div className="mb-2">
        <span className="text-xs text-[#64748b]">申请人 | Requester</span>
        <div className="text-sm text-[#94a3b8]">{request.requester}</div>
      </div>

      {/* Created At */}
      <div className="mb-3">
        <span className="text-xs text-[#64748b]">创建时间 | Created</span>
        <div className="text-xs text-[#64748b]">
          {new Date(request.created_at).toLocaleString()}
        </div>
      </div>

      {/* Reviewer Info */}
      {request.reviewer && (
        <div className="mb-3 p-2 bg-[#0f172a] rounded border border-[#1e293b]">
          <div className="text-xs text-[#64748b]">
            审批人 | Reviewer: {request.reviewer}
          </div>
          {request.comments && (
            <div className="text-xs text-[#94a3b8] mt-1">
              意见 | Comments: {request.comments}
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {isPending && (
        <div className="border-t border-[#334155] pt-3 mt-3">
          {showComments ? (
            <div className="space-y-2">
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="输入意见 | Enter comments..."
                className="w-full p-2 bg-[#0f172a] border border-[#334155] rounded text-sm text-[#e2e8f0] placeholder-[#64748b] focus:border-[#3b82f6] focus:outline-none"
                rows={2}
              />
              <div className="flex gap-2">
                <button
                  onClick={handleApprove}
                  disabled={isProcessing}
                  className="flex-1 px-3 py-1.5 bg-[#10b981] hover:bg-[#059669] text-white rounded text-sm font-medium transition-colors disabled:opacity-50"
                >
                  {isProcessing ? '处理中...' : '批准 | Approve'}
                </button>
                <button
                  onClick={handleReject}
                  disabled={isProcessing}
                  className="flex-1 px-3 py-1.5 bg-[#ef4444] hover:bg-[#dc2626] text-white rounded text-sm font-medium transition-colors disabled:opacity-50"
                >
                  {isProcessing ? '处理中...' : '拒绝 | Reject'}
                </button>
                <button
                  onClick={() => {
                    setShowComments(false);
                    setComments('');
                  }}
                  disabled={isProcessing}
                  className="px-3 py-1.5 bg-[#475569] hover:bg-[#334155] text-white rounded text-sm font-medium transition-colors disabled:opacity-50"
                >
                  取消 | Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowComments(true)}
              className="w-full px-3 py-1.5 bg-[#3b82f6] hover:bg-[#2563eb] text-white rounded text-sm font-medium transition-colors"
            >
              处理审批 | Process Approval
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ApprovalCard;
