import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL, TraceSpan } from '../types/api';

const fetchTraces = async (): Promise<TraceSpan[]> => {
  // 后端 API: GET /api/traces?limit=10 返回 TraceResponse[] 数组
  // TraceResponse 包含 { id, name, duration_ms, tags, children }
  const response = await fetch(`${API_BASE_URL}/api/traces?limit=20`);
  if (!response.ok) {
    throw new Error('获取追踪记录失败');
  }
  const data = await response.json();
  // 将后端 TraceResponse 映射为前端 TraceSpan
  return (data || []).map((trace: any) => ({
    name: trace.name,
    time: trace.tags?.started_at ? new Date(trace.tags.started_at).toLocaleTimeString() : 'N/A',
    duration: trace.duration_ms ? `${trace.duration_ms.toFixed(0)}ms` : 'N/A',
    color: getTraceColor(trace.name),
  }));
};

// 根据 span 名称获取颜色类别
const getTraceColor = (name: string): string => {
  const lowerName = name.toLowerCase();
  if (lowerName.includes('layer 1') || lowerName.includes('classific')) {
    return 'from-[rgba(16,185,129,0.4)] to-[rgba(16,185,129,0.7)]'; // Green
  }
  if (lowerName.includes('layer 2') || lowerName.includes('retriev') || lowerName.includes('chroma')) {
    return 'from-[rgba(168,85,247,0.4)] to-[rgba(168,85,247,0.7)]'; // Purple
  }
  if (lowerName.includes('layer 3') || lowerName.includes('generat') || lowerName.includes('analys')) {
    return 'from-[rgba(249,115,22,0.4)] to-[rgba(249,115,22,0.7)]'; // Orange
  }
  if (lowerName.includes('agent') || lowerName.includes('review') || lowerName.includes('decis')) {
    return 'from-[rgba(59,130,246,0.4)] to-[rgba(59,130,246,0.7)]'; // Blue
  }
  return 'from-[rgba(34,197,94,0.4)] to-[rgba(34,197,94,0.7)]'; // Default
};

export const useTraces = (traceId: string | null) => {
  return useQuery<TraceSpan[], Error>({
    queryKey: ['traces', traceId],
    queryFn: fetchTraces,
    enabled: !!traceId,
  });
};
