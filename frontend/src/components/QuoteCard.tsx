/**
 * 报价卡片组件
 *
 * 功能:
 * - 显示报价单摘要信息
 * - 支持点击查看详情
 * - 显示状态标签
 */
import React from 'react';
import type { Quote } from '../types/quote';

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
    draft: '草稿 | Draft',
    pending: '待发送 | Pending',
    sent: '已发送 | Sent',
    accepted: '已接受 | Accepted',
    rejected: '已拒绝 | Rejected',
    expired: '已过期 | Expired',
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
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getItemsCountIcon = (count: number): string => {
  if (count === 0) return '📦';
  if (count <= 3) return '📦';
  if (count <= 10) return '📦📦';
  return '📦📦📦';
};

// ============================================================================
// QuoteCard Component
// ============================================================================

export interface QuoteCardProps {
  quote: Quote;
  onClick: (quoteId: string) => void;
}

const QuoteCard: React.FC<QuoteCardProps> = ({ quote, onClick }) => {
  const statusClass = getStatusClass(quote.status);
  const statusLabel = getStatusLabel(quote.status);
  const itemsCount = quote.items?.length || 0;

  return (
    <div
      className={`p-4 rounded-xl border transition-all cursor-pointer ${
        quote.status === 'pending' || quote.status === 'sent'
          ? 'bg-gradient-to-br from-[#1e293b] to-[#0f172a] border-[#334155] hover:border-[#60a5fa]'
          : 'bg-[#0f172a] border-[#1e293b] opacity-80'
      }`}
      onClick={() => onClick(quote.quote_id)}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <span className="text-2xl">📋</span>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-[#e2e8f0] truncate">
              {quote.quote_id}
            </h3>
            <p className="text-xs text-[#94a3b8] mt-0.5 truncate">
              {quote.customer_name || quote.company}
            </p>
          </div>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium border whitespace-nowrap ${statusClass}`}>
          {statusLabel}
        </span>
      </div>

      {/* Amount */}
      <div className="mb-3">
        <div className="text-2xl font-bold text-[#60a5fa] font-mono">
          {formatCurrency(quote.total_amount, quote.currency)}
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="text-xs">
          <span className="text-[#64748b]">客户 | Customer</span>
          <p className="text-[#e2e8f0] truncate text-xs mt-0.5">{quote.customer_name || '-'}</p>
        </div>
        <div className="text-xs">
          <span className="text-[#64748b]">公司 | Company</span>
          <p className="text-[#e2e8f0] truncate text-xs mt-0.5">{quote.company || '-'}</p>
        </div>
        <div className="text-xs">
          <span className="text-[#64748b]">产品 | Products</span>
          <p className="text-[#e2e8f0] text-xs mt-0.5">
            {getItemsCountIcon(itemsCount)} {itemsCount} items
          </p>
        </div>
        <div className="text-xs">
          <span className="text-[#64748b]">有效期 | Valid Until</span>
          <p className="text-[#e2e8f0] text-xs mt-0.5">{formatDate(quote.valid_until)}</p>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-[#64748b] pt-2 border-t border-[#1e293b]">
        <span>ID: {quote.quote_id}</span>
        <span>{formatDate(quote.created_at)}</span>
      </div>
    </div>
  );
};

export default QuoteCard;
