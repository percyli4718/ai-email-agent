import React, { useState } from 'react';
import { generateEmails } from '../services/emailGenerator';
import type { GeneratedEmail } from '../types/generator';

// ============================================================================
// Props Interface
// ============================================================================

export interface GenerateEmailPanelProps {
  onEmailsGenerated?: (emails: GeneratedEmail[]) => void;
}

// ============================================================================
// GenerateEmailPanel Component
// ============================================================================

const GenerateEmailPanel: React.FC<GenerateEmailPanelProps> = ({
  onEmailsGenerated,
}) => {
  // State
  const [count, setCount] = useState<number>(1);
  const [autoProcess, setAutoProcess] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Count options for dropdown
  const countOptions = [1, 3, 5, 10, 20, 50];

  // Handle generate
  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await generateEmails({
        count,
        auto_process: autoProcess,
      });

      onEmailsGenerated?.(response.generated_emails);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成失败');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
        <h2 className="text-lg font-semibold text-[#e2e8f0]">
          生成邮件 | Generate Emails
        </h2>
      </div>

      {/* Content */}
      <div className="p-5 space-y-4">
        {/* Count Selector */}
        <div className="flex items-center gap-3">
          <label className="text-sm text-[#94a3b8] min-w-[80px]">
            数量 | Count:
          </label>
          <select
            value={count}
            onChange={(e) => setCount(Number(e.target.value))}
            disabled={isGenerating}
            className="bg-[#0f172a] border border-[#334155] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] focus:outline-none focus:border-[#3b82f6] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {countOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        {/* Auto Process Checkbox */}
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoProcess}
              onChange={(e) => setAutoProcess(e.target.checked)}
              disabled={isGenerating}
              className="w-4 h-4 rounded border-[#334155] bg-[#0f172a] text-[#3b82f6] focus:ring-[#3b82f6] focus:ring-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <span className="text-sm text-[#94a3b8]">
              自动处理 | Auto-process
            </span>
          </label>
        </div>

        {/* Help Text */}
        <div className="text-xs text-[#64748b]">
          当前模式 | Mode:{' '}
          <span className={autoProcess ? 'text-[#10b981]' : 'text-[#f59e0b]'}>
            {autoProcess ? '自动处理' : '手动处理'}
          </span>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-[rgba(239,68,68,0.1)] border border-[#ef4444] rounded-lg px-4 py-3 text-sm text-[#ef4444]">
            {error}
          </div>
        )}

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="w-full bg-[#3b82f6] hover:bg-[#2563eb] disabled:bg-[#475569] disabled:cursor-not-allowed text-[#e2e8f0] font-medium py-3 px-4 rounded-lg transition-all flex items-center justify-center gap-2"
        >
          {isGenerating ? (
            <>
              {/* Spinner */}
              <svg
                className="animate-spin h-5 w-5 text-[#e2e8f0]"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              生成中... | Generating...
            </>
          ) : (
            <>
              生成邮件 | Generate Emails
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default GenerateEmailPanel;
