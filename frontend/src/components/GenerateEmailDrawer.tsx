import React, { useState } from 'react';
import { generateEmails } from '../services/emailGenerator';
import type { GeneratedEmail } from '../types/generator';

// ============================================================================
// Props Interface
// ============================================================================

export interface GenerateEmailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onEmailsGenerated?: (emails: GeneratedEmail[]) => void;
}

// ============================================================================
// Components
// ============================================================================

/**
 * 生成邮件 Drawer - 现代化 UX 设计
 *
 * 功能:
 * - 侧边抽屉式布局，不占用主界面空间
 * - 动画过渡效果
 * - 生成参数配置
 * - 实时状态反馈
 */
const GenerateEmailDrawer: React.FC<GenerateEmailDrawerProps> = ({
  isOpen,
  onClose,
  onEmailsGenerated,
}) => {
  // State
  const [count, setCount] = useState<number>(5);
  const [autoProcess, setAutoProcess] = useState<boolean>(true);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedCount, setGeneratedCount] = useState<number>(0);

  // Count options for dropdown
  const countOptions = [1, 3, 5, 10, 20, 50];

  // Handle generate
  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setGeneratedCount(0);

    try {
      const response = await generateEmails({
        count,
        auto_process: autoProcess,
      });

      setGeneratedCount(response.generated_emails.length);
      onEmailsGenerated?.(response.generated_emails);

      // 成功后 1.5 秒自动关闭
      setTimeout(() => {
        setIsGenerating(false);
        onClose();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成失败');
      setIsGenerating(false);
    }
  };

  // Handle close
  const handleClose = () => {
    if (!isGenerating) {
      onClose();
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity duration-300 ${
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={handleClose}
      />

      {/* Drawer */}
      <div
        className={`fixed right-0 top-0 h-full w-full max-w-md bg-gradient-to-b from-[#1e293b] to-[#0f172a] border-l border-[#334155] shadow-2xl z-50 transform transition-transform duration-300 ease-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-[#334155]">
          <div>
            <h2 className="text-xl font-bold text-[#e2e8f0] flex items-center gap-2">
              <span className="text-2xl">✨</span>
              生成测试邮件
            </h2>
            <p className="text-xs text-[#64748b] mt-1">用于测试的模拟邮件数据</p>
          </div>
          <button
            onClick={handleClose}
            disabled={isGenerating}
            className="p-2 hover:bg-[#334155] rounded-lg transition-colors disabled:opacity-50"
            title="关闭"
          >
            <svg className="w-5 h-5 text-[#94a3b8]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Count Selector Card */}
          <div className="bg-[#0f172a] border border-[#334155] rounded-xl p-4">
            <label className="block text-sm font-medium text-[#94a3b8] mb-3">
              📦 生成数量
            </label>
            <select
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              disabled={isGenerating}
              className="w-full bg-[#1e293b] border border-[#475569] rounded-lg px-4 py-3 text-[#e2e8f0] font-medium focus:outline-none focus:border-[#3b82f6] focus:ring-2 focus:ring-[#3b82f6]/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {countOptions.map((option) => (
                <option key={option} value={option}>
                  {option} 封邮件
                </option>
              ))}
            </select>
            <p className="text-xs text-[#64748b] mt-2">
              建议：测试时使用 5-10 封，压力测试可使用 50 封
            </p>
          </div>

          {/* Auto Process Card */}
          <div className="bg-[#0f172a] border border-[#334155] rounded-xl p-4">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={autoProcess}
                onChange={(e) => setAutoProcess(e.target.checked)}
                disabled={isGenerating}
                className="w-5 h-5 mt-0.5 rounded border-[#475569] bg-[#1e293b] text-[#3b82f6] focus:ring-[#3b82f6] focus:ring-offset-0 disabled:opacity-50 transition-all"
              />
              <div>
                <div className="text-sm font-medium text-[#e2e8f0]">
                  🤖 自动处理
                </div>
                <div className="text-xs text-[#64748b] mt-1">
                  {autoProcess
                    ? '生成后立即启动 AI 分析流程'
                    : '生成后保持待处理状态，手动触发分析'}
                </div>
              </div>
            </label>
          </div>

          {/* Mode Indicator */}
          <div className="flex items-center gap-3 p-4 bg-[#0f172a] border border-[#334155] rounded-xl">
            <div className={`w-3 h-3 rounded-full ${autoProcess ? 'bg-[#10b981]' : 'bg-[#f59e0b]'} animate-pulse`} />
            <div>
              <div className="text-xs text-[#64748b]">当前模式</div>
              <div className={`text-sm font-medium ${autoProcess ? 'text-[#10b981]' : 'text-[#f59e0b]'}`}>
                {autoProcess ? '自动处理模式' : '手动处理模式'}
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-[rgba(239,68,68,0.1)] border border-[#ef4444] rounded-xl px-4 py-3">
              <div className="flex items-start gap-3">
                <span className="text-xl">❌</span>
                <div>
                  <div className="text-sm font-medium text-[#ef4444]">生成失败</div>
                  <div className="text-xs text-[#fca5a5] mt-1">{error}</div>
                </div>
              </div>
            </div>
          )}

          {/* Success Message */}
          {generatedCount > 0 && (
            <div className="bg-[rgba(16,185,129,0.1)] border border-[#10b981] rounded-xl px-4 py-3">
              <div className="flex items-start gap-3">
                <span className="text-xl">✅</span>
                <div>
                  <div className="text-sm font-medium text-[#10b981]">生成成功</div>
                  <div className="text-xs text-[#6ee7b7] mt-1">
                    已生成 {generatedCount} 封测试邮件
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className={`w-full py-4 px-6 rounded-xl font-semibold text-white transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:transform-none disabled:cursor-not-allowed ${
              isGenerating
                ? 'bg-[#475569]'
                : 'bg-gradient-to-r from-[#3b82f6] to-[#2563eb] hover:from-[#2563eb] hover:to-[#1d4ed8] shadow-lg hover:shadow-xl hover:shadow-[#3b82f6]/25'
            }`}
          >
            {isGenerating ? (
              <div className="flex items-center justify-center gap-3">
                <svg
                  className="animate-spin h-5 w-5 text-white"
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
                生成中...
              </div>
            ) : (
              <div className="flex items-center justify-center gap-2">
                <span>🚀</span>
                开始生成
              </div>
            )}
          </button>

          {/* Tips */}
          <div className="p-4 bg-[#0f172a] border border-[#334155] rounded-xl">
            <div className="text-xs text-[#64748b] space-y-1">
              <div>💡 提示：生成的邮件将自动出现在收件箱列表中</div>
              <div>💡 每封邮件包含随机的产品类型、区域和客户信息</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default GenerateEmailDrawer;
