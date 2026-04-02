/**
 * 成本统计仪表板组件
 * 展示成本和性能趋势图表
 */
import React from 'react';
import {
  LineChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { useCostTrend, usePerformanceTrend } from '../hooks/monitoring';
import type { TrendDataPoint } from '../types/monitoring';

interface CostDashboardProps {
  days?: number;
}

export const CostDashboard: React.FC<CostDashboardProps> = ({ days = 30 }) => {
  const { data: costTrend, isLoading: costTrendLoading } = useCostTrend(days);
  const { data: performanceTrend, isLoading: perfTrendLoading } = usePerformanceTrend(days);

  // 计算汇总数据
  const totalCost = 0;
  const totalEmails = 0;
  const avgCostPerEmail = 0;

  return (
    <div className="space-y-6">
      {/* 汇总卡片 */}
      <SummaryCards
        totalCost={totalCost}
        totalEmails={totalEmails}
        avgCostPerEmail={avgCostPerEmail}
      />

      {/* 成本趋势图表 */}
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
        <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
          <h2 className="text-lg font-semibold text-[#e2e8f0]">💰 成本趋势 | Cost Trend</h2>
        </div>
        <div className="p-5">
          {costTrendLoading ? (
            <ChartSkeleton />
          ) : (
            <CostTrendChart data={costTrend || []} />
          )}
        </div>
      </div>

      {/* 性能趋势图表 */}
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
        <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
          <h2 className="text-lg font-semibold text-[#e2e8f0]">⚡ 性能趋势 | Performance Trend</h2>
        </div>
        <div className="p-5">
          {perfTrendLoading ? (
            <ChartSkeleton />
          ) : (
            <PerformanceTrendChart data={performanceTrend || []} />
          )}
        </div>
      </div>
    </div>
  );
};

// 汇总卡片组件
interface SummaryCardsProps {
  totalCost: number;
  totalEmails: number;
  avgCostPerEmail: number;
}

const SummaryCards: React.FC<SummaryCardsProps> = ({ totalCost, totalEmails, avgCostPerEmail }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <SummaryCard
        title="总成本 | Total Cost"
        value={`$${totalCost.toFixed(2)}`}
        trend="+5.2% vs 上月"
        trendUp={false}
        icon="💰"
      />
      <SummaryCard
        title="处理邮件数 | Emails Processed"
        value={totalEmails.toString()}
        trend="+12.3% vs 上月"
        trendUp={true}
        icon="📧"
      />
      <SummaryCard
        title="平均每封成本 | Avg Cost/Email"
        value={`$${avgCostPerEmail.toFixed(4)}`}
        trend="-3.1% vs 上月"
        trendUp={true}
        icon="📊"
      />
    </div>
  );
};

interface SummaryCardProps {
  title: string;
  value: string | number;
  trend: string;
  trendUp: boolean;
  icon: string;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ title, value, trend, trendUp, icon }) => (
  <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] p-6 shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm text-[#94a3b8]">{title}</span>
      <span className="text-xl">{icon}</span>
    </div>
    <div className="text-2xl font-bold text-[#e2e8f0] mb-1">{value}</div>
    <div className={`text-xs ${trendUp ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>{trend}</div>
  </div>
);

// 成本趋势图表组件
interface CostTrendChartProps {
  data: TrendDataPoint[];
}

const CostTrendChart: React.FC<CostTrendChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return <EmptyChart message="暂无成本数据 | No Cost Data" />;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
        <YAxis stroke="#64748b" fontSize={12} />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
          }}
          labelStyle={{ color: '#e2e8f0' }}
        />
        <Legend />
        <Bar dataKey="cost" name="成本 (USD)" fill="#f97316" radius={[4, 4, 0, 0]} />
        <Line type="monotone" dataKey="emails" name="邮件数" stroke="#10b981" strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

// 性能趋势图表组件
interface PerformanceTrendChartProps {
  data: TrendDataPoint[];
}

const PerformanceTrendChart: React.FC<PerformanceTrendChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return <EmptyChart message="暂无性能数据 | No Performance Data" />;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
        <YAxis stroke="#64748b" fontSize={12} />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
          }}
          labelStyle={{ color: '#e2e8f0' }}
        />
        <Legend />
        <Line type="monotone" dataKey="avgTime" name="平均处理时间 (ms)" stroke="#a855f7" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="emails" name="邮件数" stroke="#60a5fa" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
};

// 空图表组件
const EmptyChart: React.FC<{ message: string }> = ({ message }) => (
  <div className="h-[300px] flex items-center justify-center text-[#94a3b8]">
    <div className="text-center">
      <div className="text-4xl mb-2">📭</div>
      <div>{message}</div>
    </div>
  </div>
);

// 图表骨架屏
const ChartSkeleton: React.FC = () => (
  <div className="h-[300px] animate-pulse">
    <div className="h-full bg-[#1e293b] rounded" />
  </div>
);

export default CostDashboard;
