/**
 * Email Detail Component
 *
 * 功能:
 * - 显示邮件完整详情
 * - 集成工作流时间线组件
 * - 显示 AI 分析结果
 * - 提供审批操作
 */
import React from 'react';
import { useWorkflow } from '../hooks/useWorkflow';
import { useEmailAnalysis } from '../hooks/useEmailAnalysis';
import { WorkflowTimeline } from '../components/WorkflowTimeline';
import type { AnalysisSection } from '../types/api';

// ============================================================================
// Types
// ============================================================================

export interface EmailDetailProps {
  emailId: string;
  onClose?: () => void;
}

// ============================================================================
// Components
// ============================================================================

/**
 * AI 分析结果面板
 */
const AnalysisPanel: React.FC<{
  title: string;
  icon: string;
  content: AnalysisSection;
  delay?: number;
}> = ({ title, icon, content, delay = 0 }) => {
  return (
    <div
      className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden animate-fade-in"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200">
        <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          <span>{icon}</span>
          {title}
        </h3>
      </div>
      <div className="p-4 space-y-3">
        {content.fields.map((field, index) => (
          <div key={index} className="flex gap-2">
            <span className="text-sm font-medium text-gray-600 min-w-[150px]">
              {field.label}:
            </span>
            <span className="text-sm text-gray-800">
              {field.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * 邮件详情头部
 */
const EmailDetailHeader: React.FC<{
  emailId: string;
  subject: string;
  from: string;
  receivedAt: string;
  onClose?: () => void;
}> = ({ emailId, subject, from, receivedAt, onClose }) => {
  return (
    <div className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white p-4 rounded-t-xl">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-xl font-bold truncate">{subject}</h2>
          <div className="mt-2 text-sm text-blue-100 space-y-1">
            <div>
              <span className="font-medium">From:</span> {from}
            </div>
            <div>
              <span className="font-medium">Received:</span>{' '}
              {new Date(receivedAt).toLocaleString()}
            </div>
            <div className="text-xs text-blue-200 font-mono">
              ID: {emailId}
            </div>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="ml-4 p-2 hover:bg-white/20 rounded-lg transition-colors"
            title="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * 邮件详情组件
 */
export const EmailDetail: React.FC<EmailDetailProps> = ({ emailId, onClose }) => {
  const { workflow, loading: workflowLoading } = useWorkflow(emailId);
  const { data: analysisSections } = useEmailAnalysis(emailId);

  // Mock email data (in real app, this would come from API)
  const emailData = {
    subject: 'Request for Quote - Pharmaceutical Products',
    from: 'customer@example.com',
    receivedAt: new Date().toISOString(),
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <EmailDetailHeader
        emailId={emailId}
        subject={emailData.subject}
        from={emailData.from}
        receivedAt={emailData.receivedAt}
        onClose={onClose}
      />

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Workflow Timeline */}
        <WorkflowTimeline workflow={workflow} loading={workflowLoading} />

        {/* AI Analysis Sections */}
        {analysisSections && analysisSections.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
              <span>🤖</span>
              AI 分析结果 | AI Analysis
            </h3>
            {analysisSections.map((section, index) => (
              <AnalysisPanel
                key={index}
                title={section.title}
                icon={section.icon || '📊'}
                content={section}
                delay={index * 100}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailDetail;
