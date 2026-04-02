/**
 * 报价生成面板组件
 *
 * 功能:
 * - 在邮件详情页显示
 * - 提供一键生成报价功能
 * - 显示报价生成状态
 * - 生成后跳转到报价详情
 */
import React, { useState } from 'react';
import { useGenerateQuote, useEmailQuotes } from '../hooks/useQuotes';
import { useQueryClient } from '@tanstack/react-query';

// ============================================================================
// Types
// ============================================================================

export interface GenerateQuotePanelProps {
  emailId: string;
  onQuoteGenerated?: (quoteId: string) => void;
}

// ============================================================================
// Main Component
// ============================================================================

const GenerateQuotePanel: React.FC<GenerateQuotePanelProps> = ({
  emailId,
  onQuoteGenerated,
}) => {
  const queryClient = useQueryClient();
  const [showExisting, setShowExisting] = useState(false);

  // Fetch existing quotes for this email
  const { data: existingQuotes = [] } = useEmailQuotes(emailId);

  // Generate quote mutation
  const generateMutation = useGenerateQuote();

  const handleGenerate = () => {
    generateMutation.mutate(emailId, {
      onSuccess: (data) => {
        // Invalidate quotes list
        queryClient.invalidateQueries({ queryKey: ['quotes'] });
        // Notify parent
        onQuoteGenerated?.(data.quote.quote_id);
      },
    });
  };

  const handleViewExisting = (quoteId: string) => {
    onQuoteGenerated?.(quoteId);
  };

  return (
    <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-xl border border-[#334155] p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-[#e2e8f0] flex items-center gap-2">
          <span className="text-lg">📋</span>
          报价操作
        </h3>
        {existingQuotes && existingQuotes.length > 0 && (
          <button
            onClick={() => setShowExisting(!showExisting)}
            className="text-xs text-[#3b82f6] hover:text-[#60a5fa] flex items-center gap-1"
          >
            {showExisting ? '隐藏' : `查看现有报价 (${existingQuotes.length})`}
            <span className={`transform transition-transform ${showExisting ? 'rotate-180' : ''}`}>
              ▼
            </span>
          </button>
        )}
      </div>

      {/* Generate Button */}
      {!generateMutation.isSuccess ? (
        <button
          onClick={handleGenerate}
          disabled={generateMutation.isPending}
          className="w-full px-4 py-3 text-sm font-medium rounded-lg bg-gradient-to-r from-[#14b8a6] to-[#06b6d4] text-white hover:from-[#0d9488] hover:to-[#0891b1] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {generateMutation.isPending ? (
            <>
              <span className="animate-spin">⏳</span>
              生成中...
            </>
          ) : (
            <>
              <span>✨</span>
              生成报价
            </>
          )}
        </button>
      ) : (
        <div className="bg-[rgba(16,185,129,0.2)] border border-[#10b981] rounded-lg p-4 text-center">
          <div className="text-[#10b981] text-sm font-medium mb-2">
            ✓ 报价已生成
          </div>
          <button
            onClick={() => {
              generateMutation.reset();
              setShowExisting(true);
            }}
            className="text-xs text-[#3b82f6] hover:text-[#60a5fa]"
          >
            生成新报价
          </button>
        </div>
      )}

      {/* Error Message */}
      {generateMutation.isError && (
        <div className="mt-3 bg-[rgba(239,68,68,0.2)] border border-[#ef4444] rounded-lg p-3 text-center">
          <div className="text-[#ef4444] text-sm">
            ✕ 生成失败 | Generation Failed
          </div>
          <div className="text-[#94a3b8] text-xs mt-1">
            {generateMutation.error?.message || 'Unknown error'}
          </div>
          <button
            onClick={handleGenerate}
            className="mt-2 text-xs text-[#3b82f6] hover:text-[#60a5fa]"
          >
            重试 | Retry
          </button>
        </div>
      )}

      {/* Existing Quotes */}
      {showExisting && existingQuotes && existingQuotes.length > 0 && (
        <div className="mt-4 space-y-2">
          <div className="text-xs text-[#94a3b8] mb-2">
            现有报价 | Existing Quotes
          </div>
          {existingQuotes.map((quote) => (
            <div
              key={quote.quote_id}
              onClick={() => handleViewExisting(quote.quote_id)}
              className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-3 cursor-pointer hover:border-[#60a5fa] transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">📋</span>
                  <div>
                    <div className="text-sm text-[#e2e8f0] font-medium">
                      {quote.quote_id}
                    </div>
                    <div className="text-xs text-[#94a3b8]">
                      {new Date(quote.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-[#10b981]">
                    {quote.currency} {quote.total_amount.toLocaleString()}
                  </div>
                  <div className="text-xs text-[#64748b]">
                    {quote.status}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default GenerateQuotePanel;
