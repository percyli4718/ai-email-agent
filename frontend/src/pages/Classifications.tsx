/**
 * 邮件分类列表页面
 *
 * 功能:
 * - 显示所有邮件的分类结果
 * - 支持按类型、优先级、区域过滤
 * - 显示 Layer 1 AI 分析详情
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL } from '../types/api';

// ============================================================================
// Types
// ============================================================================

interface Classification {
  id: string;
  email_id: string;
  subject: string;
  from_address: string;
  received_at: string;
  type: string;
  priority_score: number;
  urgency: string;
  language: string;
  customer_region: string;
  requires_human: boolean;
  suggested_route: string;
  products_mentioned: string[];
  status: string;
}

interface ClassificationsResponse {
  classifications: Classification[];
  total: number;
}

type FilterType = 'all' | 'inquiry' | 'complaint' | 'question' | 'contract' | 'other';
type FilterRoute = 'all' | 'quote_flow' | 'complaint_flow' | 'auto_reply' | 'manual';

// ============================================================================
// Helper Functions
// ============================================================================

const getTypeIcon = (type: string): string => {
  const icons: Record<string, string> = {
    inquiry: '📧',
    complaint: '⚠️',
    question: '❓',
    contract: '📄',
    other: '📝',
  };
  return icons[type] || '📝';
};

const getTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    inquiry: '询盘 | Inquiry',
    complaint: '投诉 | Complaint',
    question: '咨询 | Question',
    contract: '合同 | Contract',
    other: '其他 | Other',
  };
  return labels[type] || type;
};

const getUrgencyClass = (urgency: string): string => {
  const classes: Record<string, string> = {
    high: 'bg-red-100 text-red-700 border-red-500',
    medium: 'bg-yellow-100 text-yellow-700 border-yellow-500',
    low: 'bg-green-100 text-green-700 border-green-500',
  };
  return classes[urgency] || classes.low;
};

const getRouteIcon = (route: string): string => {
  const icons: Record<string, string> = {
    quote_flow: '💰',
    complaint_flow: '⚠️',
    auto_reply: '🤖',
    manual: '👤',
  };
  return icons[route] || '📝';
};

const getRouteLabel = (route: string): string => {
  const labels: Record<string, string> = {
    quote_flow: '报价流程 | Quote Flow',
    complaint_flow: '投诉流程 | Complaint Flow',
    auto_reply: '自动回复 | Auto Reply',
    manual: '人工处理 | Manual',
  };
  return labels[route] || route;
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * 分类详情弹窗
 */
const ClassificationDetailModal: React.FC<{
  classification: Classification;
  onClose: () => void;
}> = ({ classification, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white p-4 rounded-t-xl">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-bold">Layer 1: 邮件分类详情</h2>
              <p className="text-blue-100 text-sm mt-1">{classification.subject}</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* 基本信息 */}
          <section>
            <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
              <span>📋</span>
              基本信息 | Basic Information
            </h3>
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-sm text-gray-600">邮件 ID</span>
                  <p className="text-sm font-medium text-gray-800">{classification.email_id}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">发件人</span>
                  <p className="text-sm font-medium text-gray-800">{classification.from_address}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">接收时间</span>
                  <p className="text-sm font-medium text-gray-800">{formatDate(classification.received_at)}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">状态</span>
                  <p className="text-sm font-medium text-gray-800">{classification.status}</p>
                </div>
              </div>
            </div>
          </section>

          {/* 分类结果 */}
          <section>
            <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
              <span>🤖</span>
              AI 分类结果 | Classification Result
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                <span className="text-xs text-blue-600">邮件类型 | Type</span>
                <p className="text-lg font-bold text-blue-800 flex items-center gap-2 mt-1">
                  <span>{getTypeIcon(classification.type)}</span>
                  {getTypeLabel(classification.type)}
                </p>
              </div>
              <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
                <span className="text-xs text-purple-600">紧急程度 | Urgency</span>
                <p className={`text-lg font-bold mt-1 inline-block px-3 py-1 rounded border ${getUrgencyClass(classification.urgency)}`}>
                  {classification.urgency}
                </p>
              </div>
              <div className="bg-green-50 rounded-lg p-3 border border-green-200">
                <span className="text-xs text-green-600">优先级评分 | Priority</span>
                <p className="text-lg font-bold text-green-800">
                  {(classification.priority_score * 100).toFixed(0)}%
                </p>
              </div>
              <div className="bg-yellow-50 rounded-lg p-3 border border-yellow-200">
                <span className="text-xs text-yellow-600">语言 | Language</span>
                <p className="text-lg font-bold text-yellow-800">{classification.language}</p>
              </div>
            </div>
          </section>

          {/* 路由决策 */}
          <section>
            <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
              <span>🔀</span>
              路由决策 | Routing Decision
            </h3>
            <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{getRouteIcon(classification.suggested_route)}</span>
                <div>
                  <p className="text-lg font-bold text-indigo-800">
                    {getRouteLabel(classification.suggested_route)}
                  </p>
                  <p className="text-sm text-indigo-600 mt-1">
                    {classification.requires_human ? '⚠️ 需要人工介入' : '✅ 可自动处理'}
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* 产品和区域 */}
          <section>
            <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
              <span>🌍</span>
              产品和区域 | Products & Region
            </h3>
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <div>
                <span className="text-sm text-gray-600">客户区域 | Customer Region</span>
                <p className="text-lg font-bold text-gray-800 mt-1">{classification.customer_region}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">提及产品 | Products Mentioned</span>
                {classification.products_mentioned && classification.products_mentioned.length > 0 ? (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {classification.products_mentioned.map((product, idx) => (
                      <span key={idx} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                        {product}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 mt-1">未提及具体产品</p>
                )}
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

/**
 * 分类卡片
 */
const ClassificationCard: React.FC<{
  classification: Classification;
  onClick: () => void;
}> = ({ classification, onClick }) => {
  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md hover:border-blue-300 transition-all cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className="text-2xl">{getTypeIcon(classification.type)}</span>
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-bold text-gray-800 truncate">
              {classification.subject}
            </h3>
            <p className="text-sm text-gray-500 truncate">{classification.from_address}</p>
          </div>
        </div>
        <span className={`px-2 py-1 rounded text-xs font-bold border ${getUrgencyClass(classification.urgency)}`}>
          {classification.urgency}
        </span>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-2 mb-3">
        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
          {getTypeLabel(classification.type)}
        </span>
        <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">
          {classification.customer_region}
        </span>
        <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs font-medium flex items-center gap-1">
          <span>{getRouteIcon(classification.suggested_route)}</span>
          {classification.suggested_route.replace('_flow', '').replace('_', ' ')}
        </span>
      </div>

      {/* Products */}
      {classification.products_mentioned && classification.products_mentioned.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {classification.products_mentioned.slice(0, 3).map((product, idx) => (
            <span key={idx} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
              {product}
            </span>
          ))}
          {classification.products_mentioned.length > 3 && (
            <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
              +{classification.products_mentioned.length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-100">
        <span>{formatDate(classification.received_at)}</span>
        <span className="flex items-center gap-1">
          <span>优先级：</span>
          <span className="font-bold text-green-600">
            {(classification.priority_score * 100).toFixed(0)}%
          </span>
        </span>
      </div>
    </div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

/**
 * 邮件分类列表页面
 */
export const Classifications: React.FC = () => {
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [filterUrgency, setFilterUrgency] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [filterRoute, setFilterRoute] = useState<FilterRoute>('all');
  const [selectedClassification, setSelectedClassification] = useState<Classification | null>(null);

  // Fetch classifications
  const { data, isLoading, error } = useQuery<ClassificationsResponse, Error>({
    queryKey: ['classifications'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/emails/classifications`);
      if (!response.ok) {
        throw new Error('获取分类列表失败');
      }
      return response.json();
    },
  });

  // Filter classifications
  const filteredClassifications = data?.classifications.filter((c) => {
    if (filterType !== 'all' && c.type !== filterType) return false;
    if (filterUrgency !== 'all' && c.urgency !== filterUrgency) return false;
    if (filterRoute !== 'all' && c.suggested_route !== filterRoute) return false;
    return true;
  }) || [];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <span>🏷️</span>
          邮件分类管理 | Email Classification
        </h1>
        <p className="text-gray-600 mt-1">
          Layer 1 AI 自动分类结果 - 共 {data?.total || 0} 封邮件
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              邮件类型 | Type
            </label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as FilterType)}
              className="w-full rounded-lg border-gray-300 border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部 | All</option>
              <option value="inquiry">📧 询盘 | Inquiry</option>
              <option value="complaint">⚠️ 投诉 | Complaint</option>
              <option value="question">❓ 咨询 | Question</option>
              <option value="contract">📄 合同 | Contract</option>
              <option value="other">📝 其他 | Other</option>
            </select>
          </div>

          {/* Urgency Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              紧急程度 | Urgency
            </label>
            <select
              value={filterUrgency}
              onChange={(e) => setFilterUrgency(e.target.value as any)}
              className="w-full rounded-lg border-gray-300 border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部 | All</option>
              <option value="high">🔴 高 | High</option>
              <option value="medium">🟡 中 | Medium</option>
              <option value="low">🟢 低 | Low</option>
            </select>
          </div>

          {/* Route Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              路由类型 | Route
            </label>
            <select
              value={filterRoute}
              onChange={(e) => setFilterRoute(e.target.value as FilterRoute)}
              className="w-full rounded-lg border-gray-300 border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部 | All</option>
              <option value="quote_flow">💰 报价流程 | Quote Flow</option>
              <option value="complaint_flow">⚠️ 投诉流程 | Complaint Flow</option>
              <option value="auto_reply">🤖 自动回复 | Auto Reply</option>
              <option value="manual">👤 人工处理 | Manual</option>
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">加载中...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
          <p className="text-red-700 font-medium">加载失败</p>
          <p className="text-sm text-red-600 mt-1">{error.message}</p>
        </div>
      )}

      {!isLoading && !error && filteredClassifications.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <p className="text-gray-600 font-medium">暂无分类数据</p>
          <p className="text-sm text-gray-500 mt-1">邮件分类后将在此显示</p>
        </div>
      )}

      {!isLoading && !error && filteredClassifications.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredClassifications.map((classification) => (
            <ClassificationCard
              key={classification.id}
              classification={classification}
              onClick={() => setSelectedClassification(classification)}
            />
          ))}
        </div>
      )}

      {/* Detail Modal */}
      {selectedClassification && (
        <ClassificationDetailModal
          classification={selectedClassification}
          onClose={() => setSelectedClassification(null)}
        />
      )}
    </div>
  );
};

export default Classifications;
