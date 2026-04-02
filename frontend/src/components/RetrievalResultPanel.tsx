/**
 * Layer 2 Retrieval Result Component
 *
 * 功能:
 * - 展示检索到的相似历史邮件
 * - 展示适用的定价政策
 * - 展示合规要求
 * - 展示客户历史记录
 */
import React, { useState } from 'react';
import { useRetrievalResult, SimilarEmail, PricingPolicy, ComplianceRequirement } from '../hooks/useRetrievalResult';

// ============================================================================
// Types
// ============================================================================

export interface RetrievalResultPanelProps {
  emailId: string;
}

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * 相似邮件卡片
 */
const SimilarEmailCard: React.FC<{
  email: SimilarEmail;
  index: number;
}> = ({ email, index }) => {
  const similarityPercent = Math.round((1 - (email.similarity || 0)) * 100);

  return (
    <div className="bg-gray-50 rounded-lg p-3 border border-gray-200 hover:border-blue-300 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-blue-600 bg-blue-100 px-2 py-0.5 rounded">
            #{index + 1}
          </span>
          <span className="text-xs text-gray-500 font-mono">
            {email.metadata?.region || 'Unknown'}
          </span>
        </div>
        <span className={`text-xs font-bold px-2 py-1 rounded ${
          similarityPercent >= 80 ? 'text-green-700 bg-green-100' :
          similarityPercent >= 60 ? 'text-yellow-700 bg-yellow-100' :
          'text-gray-700 bg-gray-100'
        }`}>
          {similarityPercent}% 相似
        </span>
      </div>
      <p className="text-sm text-gray-700 line-clamp-3 mb-2">
        {email.content}
      </p>
      {email.metadata?.type && (
        <span className="text-xs text-gray-500">
          类型：{email.metadata.type}
        </span>
      )}
    </div>
  );
};

/**
 * 相似邮件列表
 */
const SimilarEmailsSection: React.FC<{
  documents: string[];
  metadatas: Record<string, any>[];
  distances?: number[];
  ids?: string[];
}> = ({ documents, metadatas, distances, ids }) => {
  const emails: SimilarEmail[] = documents.map((content, index) => ({
    id: ids?.[index] || `email_${index}`,
    content,
    similarity: distances ? 1 - distances[index] : 0.5,
    metadata: metadatas[index] || {},
  }));

  if (!documents || documents.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        <svg className="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <p className="text-sm">未找到相似邮件</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {emails.map((email, index) => (
        <SimilarEmailCard key={email.id} email={email} index={index} />
      ))}
    </div>
  );
};

/**
 * 定价政策表格
 */
const PricingPolicyTable: React.FC<{
  policies: PricingPolicy[];
  region: string;
}> = ({ policies, region }) => {
  if (!policies || policies.length === 0) {
    return (
      <div className="text-center py-4 text-gray-400">
        <p className="text-sm">该区域暂无定价政策</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-2 px-3 font-semibold text-gray-700">产品</th>
            <th className="text-right py-2 px-3 font-semibold text-gray-700">基准价</th>
            <th className="text-right py-2 px-3 font-semibold text-gray-700">折扣率</th>
            <th className="text-right py-2 px-3 font-semibold text-gray-700">货币</th>
          </tr>
        </thead>
        <tbody>
          {policies.map((policy, index) => (
            <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-2 px-3 text-gray-800">{policy.product}</td>
              <td className="py-2 px-3 text-right text-gray-800 font-medium">
                ${policy.base_price.toFixed(2)}
              </td>
              <td className="py-2 px-3 text-right">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  policy.discount_rate > 0.05 ? 'text-green-700 bg-green-100' :
                  policy.discount_rate > 0 ? 'text-blue-700 bg-blue-100' :
                  'text-gray-600 bg-gray-100'
                }`}>
                  {(policy.discount_rate * 100).toFixed(0)}%
                </span>
              </td>
              <td className="py-2 px-3 text-right text-gray-600">{policy.currency}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

/**
 * 合规要求列表
 */
const ComplianceRequirementsSection: React.FC<{
  requirements: ComplianceRequirement[];
  region: string;
}> = ({ requirements, region }) => {
  if (!requirements || requirements.length === 0) {
    return (
      <div className="text-center py-4 text-gray-400">
        <p className="text-sm">该区域暂无特殊合规要求</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {requirements.map((req, index) => (
        <div
          key={index}
          className={`p-3 rounded-lg border-l-4 ${
            req.mandatory
              ? 'bg-red-50 border-red-500'
              : 'bg-yellow-50 border-yellow-500'
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-bold text-gray-800">
                  {req.name}
                </span>
                {req.mandatory && (
                  <span className="text-xs font-bold text-red-700 bg-red-100 px-2 py-0.5 rounded">
                    必需
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-600 mb-1">
                类型：{req.type}
              </p>
              {req.description && (
                <p className="text-xs text-gray-700">
                  {req.description}
                </p>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * 客户历史卡片
 */
const CustomerHistoryCard: React.FC<{
  customer: {
    name?: string;
    tier?: string;
    region?: string;
  } | null;
}> = ({ customer }) => {
  if (!customer) {
    return (
      <div className="text-center py-4 text-gray-400">
        <p className="text-sm">新客户或未找到历史记录</p>
      </div>
    );
  }

  const tierColor = {
    A: 'text-green-700 bg-green-100',
    B: 'text-blue-700 bg-blue-100',
    C: 'text-yellow-700 bg-yellow-100',
  }[customer.tier || 'C'];

  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-lg font-bold text-gray-800">{customer.name || 'Unknown Customer'}</p>
          <p className="text-sm text-gray-600 mt-1">区域：{customer.region || 'Unknown'}</p>
        </div>
        <span className={`text-sm font-bold px-3 py-1 rounded-full ${tierColor}`}>
          Tier {customer.tier || 'C'}
        </span>
      </div>
    </div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

/**
 * Layer 2 检索结果面板
 */
export const RetrievalResultPanel: React.FC<RetrievalResultPanelProps> = ({ emailId }) => {
  const { data, isLoading, error } = useRetrievalResult(emailId);
  const [activeTab, setActiveTab] = useState<'overview' | 'pricing' | 'compliance' | 'similar'>('overview');

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3 mx-auto"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-center">
        <p className="text-red-700 font-medium">加载检索结果失败</p>
        <p className="text-sm text-red-600 mt-1">{error.message}</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const tabs = [
    { id: 'overview', label: '概览', icon: '📊' },
    { id: 'pricing', label: '定价政策', icon: '💰' },
    { id: 'compliance', label: '合规要求', icon: '✅' },
    { id: 'similar', label: '相似邮件', icon: '📧' },
  ] as const;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gradient-to-r from-indigo-50 to-purple-50 border-b border-gray-200">
        <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          <span>🔍</span>
          Layer 2: 上下文检索结果 | Context Retrieval
        </h3>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 bg-gray-50">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-white text-indigo-600 border-t-2 border-indigo-600'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <span className="mr-1">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-4">
            {/* Customer History */}
            <section>
              <h4 className="text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                <span>👤</span>
                客户历史 | Customer History
              </h4>
              <CustomerHistoryCard customer={data.customer_history} />
            </section>

            {/* Pricing Summary */}
            <section>
              <h4 className="text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                <span>💰</span>
                定价政策摘要 | Pricing Summary
              </h4>
              <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">区域：{data.pricing_policy.region}</span>
                  <span className="text-gray-800 font-medium">
                    {data.pricing_policy.policies.length} 个产品
                  </span>
                </div>
              </div>
            </section>

            {/* Compliance Summary */}
            <section>
              <h4 className="text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                <span>✅</span>
                合规要求摘要 | Compliance Summary
              </h4>
              <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">区域：{data.compliance.region}</span>
                  <span className="text-gray-800 font-medium">
                    {data.compliance.requirements.length} 项要求
                  </span>
                </div>
                {data.compliance.requirements.some(r => r.mandatory) && (
                  <div className="mt-2 text-xs text-red-600 font-medium">
                    ⚠️ 包含必需合规要求
                  </div>
                )}
              </div>
            </section>

            {/* Similar Emails Summary */}
            <section>
              <h4 className="text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                <span>📧</span>
                相似邮件 | Similar Emails
              </h4>
              <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                <p className="text-sm text-gray-700">
                  找到 {data.similar_emails.documents.length} 封相似历史邮件
                </p>
              </div>
            </section>
          </div>
        )}

        {/* Pricing Tab */}
        {activeTab === 'pricing' && (
          <div>
            <div className="mb-3 text-sm text-gray-600">
              区域：<span className="font-medium">{data.pricing_policy.region}</span>
            </div>
            <PricingPolicyTable
              policies={data.pricing_policy.policies}
              region={data.pricing_policy.region}
            />
          </div>
        )}

        {/* Compliance Tab */}
        {activeTab === 'compliance' && (
          <div>
            <div className="mb-3 text-sm text-gray-600">
              区域：<span className="font-medium">{data.compliance.region}</span>
            </div>
            <ComplianceRequirementsSection
              requirements={data.compliance.requirements}
              region={data.compliance.region}
            />
          </div>
        )}

        {/* Similar Emails Tab */}
        {activeTab === 'similar' && (
          <SimilarEmailsSection
            documents={data.similar_emails.documents}
            metadatas={data.similar_emails.metadatas}
            distances={data.similar_emails.distances}
            ids={data.similar_emails.ids}
          />
        )}
      </div>
    </div>
  );
};

export default RetrievalResultPanel;
