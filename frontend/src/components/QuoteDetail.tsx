/**
 * 报价详情组件
 *
 * 功能:
 * - 显示报价单的完整信息
 * - 显示报价项目列表（产品、单价、数量、总价）
 * - 显示条款信息
 * - 支持状态更新操作
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { API_BASE_URL } from '../types/api';
import type { Quote, QuoteItem } from '../types/quote';

// ============================================================================
// Types
// ============================================================================

export interface QuoteDetailProps {
  quoteId: string;
  onBack?: () => void;
  onStatusUpdated?: (quoteId: string, status: string) => void;
}

// ============================================================================
// Helper Functions
// ============================================================================

const getStatusClass = (status: string): string => {
  const classes: Record<string, string> = {
    draft: 'bg-[rgba(100,116,139,0.2)] text-[#94a3b8] border-[#94a3b8]',
    pending: 'bg-[rgba(245,158,11,0.2)] text-[#f59e0b] border-[#f59e0b]',
    sent: 'bg-[rgba(59,130,246,0.2)] text-[#3b82f6] border-[#3b82f6]',
    accepted: 'bg-[rgba(16,185,129,0.2)] text-[#10b981] border-[#10b981]',
    rejected: 'bg-[rgba(239,68,68,0.2)] text-[#ef4444] border-[#ef4444]',
    expired: 'bg-[rgba(100,116,139,0.2)] text-[#64748b] border-[#64748b]',
  };
  return classes[status] || classes.draft;
};

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    draft: '草稿',
    pending: '待发送',
    sent: '已发送',
    accepted: '已接受',
    rejected: '已拒绝',
    expired: '已过期',
  };
  return labels[status] || status;
};

const formatCurrency = (amount: number, currency: string): string => {
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
  className?: string;
}

const DetailSection: React.FC<DetailSectionProps> = ({ title, icon, children, className = '' }) => (
  <div className={`bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-xl border border-[#334155] p-5 ${className}`}>
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
// Quote Items Table Component
// ============================================================================

interface QuoteItemsTableProps {
  items: QuoteItem[];
  currency: string;
}

const QuoteItemsTable: React.FC<QuoteItemsTableProps> = ({ items, currency }) => (
  <div className="overflow-x-auto">
    <table className="w-full text-xs">
      <thead>
        <tr className="border-b border-[#334155]">
          <th className="text-left py-2 px-3 text-[#94a3b8] font-medium">#</th>
          <th className="text-left py-2 px-3 text-[#94a3b8] font-medium">产品 | Product</th>
          <th className="text-left py-2 px-3 text-[#94a3b8] font-medium">规格 | Specification</th>
          <th className="text-right py-2 px-3 text-[#94a3b8] font-medium">数量 | Qty</th>
          <th className="text-right py-2 px-3 text-[#94a3b8] font-medium">单价 | Unit Price</th>
          <th className="text-right py-2 px-3 text-[#94a3b8] font-medium">金额 | Amount</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item, index) => (
          <tr key={index} className="border-b border-[#1e293b] last:border-0">
            <td className="py-3 px-3 text-[#64748b]">{index + 1}</td>
            <td className="py-3 px-3 text-[#e2e8f0]">{item.product_name}</td>
            <td className="py-3 px-3 text-[#94a3b8]">{item.specification}</td>
            <td className="py-3 px-3 text-right text-[#e2e8f0]">
              {item.quantity} {item.unit}
            </td>
            <td className="py-3 px-3 text-right text-[#94a3b8]">
              {formatCurrency(item.unit_price, currency)}
            </td>
            <td className="py-3 px-3 text-right font-medium text-[#60a5fa]">
              {formatCurrency(item.amount, currency)}
            </td>
          </tr>
        ))}
      </tbody>
      <tfoot>
        <tr className="border-t border-[#475569]">
          <td colSpan={5} className="py-3 px-3 text-right text-[#94a3b8] font-medium">
            总计 | Total
          </td>
          <td className="py-3 px-3 text-right text-lg font-bold text-[#10b981]">
            {formatCurrency(items.reduce((sum, item) => sum + item.amount, 0), currency)}
          </td>
        </tr>
      </tfoot>
    </table>
  </div>
);

// ============================================================================
// Main Component
// ============================================================================

const QuoteDetail: React.FC<QuoteDetailProps> = ({
  quoteId,
  onBack,
  onStatusUpdated,
}) => {
  const queryClient = useQueryClient();
  const [showStatusUpdate, setShowStatusUpdate] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);

  // Fetch quote details
  const { data: quote, isLoading, error } = useQuery<Quote>({
    queryKey: ['quote', quoteId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/quotes/${quoteId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch quote details');
      }
      return response.json();
    },
  });

  // Update status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      fetch(`${API_BASE_URL}/quotes/${id}/status?status=${status}`, {
        method: 'POST',
      }).then(res => {
        if (!res.ok) throw new Error('Failed to update status');
        return res.json();
      }),
    onSuccess: (_, { id, status }) => {
      queryClient.invalidateQueries({ queryKey: ['quote', id] });
      queryClient.invalidateQueries({ queryKey: ['quotes'] });
      onStatusUpdated?.(id, status);
      setShowStatusUpdate(false);
      setSelectedStatus(null);
    },
  });

  const handleStatusUpdate = (status: string) => {
    setSelectedStatus(status);
    updateStatusMutation.mutate({ id: quoteId, status });
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-[#334155] rounded w-1/3"></div>
          <div className="h-32 bg-[#334155] rounded"></div>
          <div className="h-48 bg-[#334155] rounded"></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !quote) {
    return (
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-xl border border-[#334155] p-8 text-center">
        <div className="text-4xl mb-4">❌</div>
        <div className="text-[#ef4444] text-lg font-medium mb-2">加载失败 | Load Failed</div>
        <div className="text-[#94a3b8] text-sm">{error?.message || '报价单不存在'}</div>
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

  const statusClass = getStatusClass(quote.status);
  const statusLabel = getStatusLabel(quote.status);

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
            <span className="text-3xl">📋</span>
            <div>
              <h2 className="text-xl font-bold text-[#e2e8f0]">{quote.quote_id}</h2>
              <p className="text-xs text-[#94a3b8]">{quote.customer_name || quote.company}</p>
            </div>
          </div>
        </div>
        <span className={`px-4 py-2 rounded-full text-sm font-medium border ${statusClass}`}>
          {statusLabel}
        </span>
      </div>

      {/* Total Amount Display */}
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-xl border border-[#334155] p-6 text-center">
        <div className="text-sm text-[#94a3b8] mb-2">报价总金额 | Total Amount</div>
        <div className="text-4xl font-bold text-[#10b981] font-mono">
          {formatCurrency(quote.total_amount, quote.currency)}
        </div>
      </div>

      {/* Items Table */}
      <DetailSection title="报价项目 | Quote Items" icon="📦">
        {quote.items && quote.items.length > 0 ? (
          <QuoteItemsTable items={quote.items} currency={quote.currency} />
        ) : (
          <div className="text-sm text-[#94a3b8] text-center py-4">
            暂无报价项目 | No items
          </div>
        )}
      </DetailSection>

      {/* Customer & Terms Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Customer Info */}
        <DetailSection title="客户信息 | Customer Info" icon="👤">
          <DetailRow label="客户姓名 | Customer Name" value={quote.customer_name || '-'} />
          <DetailRow label="电子邮箱 | Email" value={quote.customer_email || '-'} />
          <DetailRow label="公司 | Company" value={quote.company || '-'} />
        </DetailSection>

        {/* Terms Info */}
        <DetailSection title="条款信息 | Terms" icon="📋">
          <DetailRow label="付款条款 | Payment Terms" value={quote.payment_terms || '-'} />
          <DetailRow label="交货时间 | Delivery Time" value={quote.delivery_time || '-'} />
          <DetailRow label="装运港 | Shipping Port" value={quote.shipping_port || '-'} />
          <DetailRow label="有效期至 | Valid Until" value={formatDate(quote.valid_until)} />
        </DetailSection>
      </div>

      {/* Notes */}
      {quote.notes && (
        <DetailSection title="备注 | Notes" icon="💡">
          <p className="text-sm text-[#e2e8f0] whitespace-pre-wrap">{quote.notes}</p>
        </DetailSection>
      )}

      {/* Timestamps */}
      <DetailSection title="时间信息 | Timestamps" icon="🕐">
        <DetailRow label="创建时间 | Created" value={formatDate(quote.created_at)} />
        <DetailRow label="更新时间 | Updated" value={formatDate(quote.updated_at)} />
      </DetailSection>

      {/* Status Update Actions */}
      {quote.status !== 'accepted' && quote.status !== 'rejected' && quote.status !== 'expired' && (
        <DetailSection title="状态操作 | Status Actions" icon="⚙️">
          {!showStatusUpdate ? (
            <button
              onClick={() => setShowStatusUpdate(true)}
              className="px-4 py-2 text-sm font-medium text-[#3b82f6] hover:text-[#60a5fa] border border-[#3b82f6] rounded-lg"
            >
              更新状态 | Update Status
            </button>
          ) : (
            <div className="space-y-3">
              <div className="text-xs text-[#94a3b8] mb-2">选择新状态:</div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleStatusUpdate('pending')}
                  disabled={updateStatusMutation.isPending}
                  className={`px-3 py-2 text-xs font-medium rounded-lg border transition-colors ${
                    quote.status === 'pending'
                      ? 'bg-[rgba(245,158,11,0.2)] text-[#f59e0b] border-[#f59e0b]'
                      : 'text-[#94a3b8] border-[#334155] hover:border-[#f59e0b]'
                  }`}
                >
                  待发送
                </button>
                <button
                  onClick={() => handleStatusUpdate('sent')}
                  disabled={updateStatusMutation.isPending}
                  className={`px-3 py-2 text-xs font-medium rounded-lg border transition-colors ${
                    quote.status === 'sent'
                      ? 'bg-[rgba(59,130,246,0.2)] text-[#3b82f6] border-[#3b82f6]'
                      : 'text-[#94a3b8] border-[#334155] hover:border-[#3b82f6]'
                  }`}
                >
                  已发送
                </button>
                <button
                  onClick={() => handleStatusUpdate('accepted')}
                  disabled={updateStatusMutation.isPending}
                  className="px-3 py-2 text-xs font-medium rounded-lg bg-[rgba(16,185,129,0.2)] text-[#10b981] border border-[#10b981] hover:bg-[rgba(16,185,129,0.3)] transition-colors"
                >
                  ✓ 已接受
                </button>
                <button
                  onClick={() => handleStatusUpdate('rejected')}
                  disabled={updateStatusMutation.isPending}
                  className="px-3 py-2 text-xs font-medium rounded-lg bg-[rgba(239,68,68,0.2)] text-[#ef4444] border border-[#ef4444] hover:bg-[rgba(239,68,68,0.3)] transition-colors"
                >
                  ✕ 已拒绝
                </button>
              </div>
              <button
                onClick={() => {
                  setShowStatusUpdate(false);
                  setSelectedStatus(null);
                }}
                className="text-xs text-[#94a3b8] hover:text-[#e2e8f0]"
              >
                取消
              </button>
            </div>
          )}
          {selectedStatus && (
            <div className="mt-3 text-xs text-[#94a3b8]">
              更新状态中... | Updating status...
            </div>
          )}
        </DetailSection>
      )}
    </div>
  );
};

export default QuoteDetail;
