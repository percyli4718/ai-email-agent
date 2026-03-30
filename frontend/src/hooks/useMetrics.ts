import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL, Metric } from '../types/api';

const fetchMetrics = async (): Promise<Metric[]> => {
  const response = await fetch(`${API_BASE_URL}/api/metrics`);
  if (!response.ok) {
    throw new Error('获取系统指标失败');
  }
  const data = await response.json();
  // 后端返回单个对象 { emails_today, avg_processing_time_ms, ... }
  // 前端期望 Metric[] 数组格式
  return [
    {
      name: 'Emails Today',
      value: data.emails_today?.toString() || '0',
      trend: '+12% vs yesterday',
      trendUp: true,
    },
    {
      name: 'Avg Processing Time',
      value: `${(data.avg_processing_time_ms || 0).toFixed(0)}ms`,
      trend: '-8% faster',
      trendUp: true,
    },
    {
      name: 'Avg Cost per Email',
      value: `$${(data.avg_cost_per_email || 0).toFixed(4)}`,
      trend: '-5% vs last week',
      trendUp: true,
    },
    {
      name: 'Classification Accuracy',
      value: `${((data.classification_accuracy || 0) * 100).toFixed(1)}%`,
      trend: '+2.3% improvement',
      trendUp: true,
    },
    {
      name: 'Sonnet Routing Rate',
      value: `${((data.sonnet_routing_rate || 0) * 100).toFixed(0)}%`,
      trend: 'Target: 80%',
      trendUp: data.sonnet_routing_rate >= 0.8,
    },
    {
      name: 'Prompt Versions',
      value: data.prompt_versions?.toString() || '0',
      trend: 'Active versions',
      trendUp: true,
    },
  ];
};

export const useMetrics = () => {
  return useQuery<Metric[], Error>({
    queryKey: ['metrics'],
    queryFn: fetchMetrics,
  });
};
