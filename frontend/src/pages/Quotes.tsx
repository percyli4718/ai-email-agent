/**
 * 报价列表页面
 *
 * 功能:
 * - 显示所有报价单列表
 * - 支持按状态过滤
 * - 支持点击查看详情
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL } from '../types/api';
import type { Quote, QuoteFilterStatus } from '../types/quote';
import QuoteCard from '../components/QuoteCard';
import QuoteDetail from '../components/QuoteDetail';

// ============================================================================
// Types
// ============================================================================

interface QuotesResponse {
  quotes: Quote[];
  total: number;
}

// ============================================================================
// Main Component
// ============================================================================

export interface QuotesProps {
  selectedQuoteId?: string | null;
  onQuoteViewed?: () => void;
}

const Quotes: React.FC<QuotesProps> = ({
  selectedQuoteId: propSelectedQuoteId = null,
  onQuoteViewed,
}) => {
  const [filter, setFilter] = useState<QuoteFilterStatus>('all');
  const [internalSelectedQuoteId, setInternalSelectedQuoteId] = useState<string | null>(null);

  // Use prop value if provided, otherwise use internal state
  const selectedQuoteId = propSelectedQuoteId !== null ? propSelectedQuoteId : internalSelectedQuoteId;

  const setSelectedQuoteId = (id: string | null) => {
    setInternalSelectedQuoteId(id);
    if (id === null && onQuoteViewed) {
      onQuoteViewed();
    }
  };

  // Fetch quotes list
  const { data, isLoading, error } = useQuery<QuotesResponse>({
    queryKey: ['quotes', filter],
    queryFn: async () => {
      const params = filter !== 'all' ? `?status=${filter}` : '';
      const response = await fetch(`${API_BASE_URL}/quotes${params}`);
      if (!response.ok) {
        throw new Error('Failed to fetch quotes');
      }
      return response.json();
    },
  });

  const handleCardClick = (quoteId: string) => {
    setSelectedQuoteId(quoteId);
  };

  const handleBack = () => {
    setSelectedQuoteId(null);
  };

  // Filter tabs
  const tabs: { key: QuoteFilterStatus; label: string; icon: string }[] = [
    { key: 'all', label: '全部', icon: '📋' },
    { key: 'draft', label: '草稿', icon: '📝' },
    { key: 'pending', label: '待发送', icon: '⏳' },
    { key: 'sent', label: '已发送', icon: '✉️' },
    { key: 'accepted', label: '已接受', icon: '✅' },
    { key: 'rejected', label: '已拒绝', icon: '❌' },
    { key: 'expired', label: '已过期', icon: '🕐' },
  ];

  // Show detail view
  if (selectedQuoteId) {
    return (
      <div>
        <QuoteDetail
          quoteId={selectedQuoteId}
          onBack={handleBack}
          onStatusUpdated={() => setSelectedQuoteId(null)}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-[#e2e8f0]">📋 报价中心 | Quotes</h2>
      </div>

      {/* Filter Tabs */}
      <div className="flex border-b border-[#334155] overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
              filter === tab.key
                ? 'text-[#3b82f6] border-b-2 border-[#3b82f6] bg-[rgba(59,130,246,0.1)]'
                : 'text-[#94a3b8] hover:text-[#e2e8f0]'
            }`}
          >
            <span className="mr-1">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-48 bg-[#334155] rounded-xl"></div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-xl border border-[#334155] p-8 text-center">
          <div className="text-4xl mb-4">❌</div>
          <div className="text-[#ef4444] text-lg font-medium mb-2">加载失败 | Load Failed</div>
          <div className="text-[#94a3b8] text-sm">{error.message}</div>
        </div>
      ) : !data?.quotes || data.quotes.length === 0 ? (
        <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-xl border border-[#334155] p-8 text-center">
          <div className="text-4xl mb-4">📭</div>
          <div className="text-[#e2e8f0] text-lg font-medium mb-2">暂无报价 | No Quotes</div>
          <div className="text-[#94a3b8] text-sm">
            {filter === 'all' ? '暂无报价单' : `暂无${filter}状态的报价`}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.quotes.map((quote) => (
            <QuoteCard
              key={quote.quote_id}
              quote={quote}
              onClick={handleCardClick}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Quotes;
