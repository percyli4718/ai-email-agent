import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL, PromptVersion } from '../types/api';

const fetchPromptVersions = async (): Promise<PromptVersion[]> => {
  const response = await fetch(`${API_BASE_URL}/prompts/versions`);
  if (!response.ok) {
    throw new Error('获取 Prompt 版本失败');
  }
  const data = await response.json();
  // 后端返回 { versions: [...], total_versions: N }
  // 将后端 PromptVersion 映射为前端格式
  return (data.versions || []).map((version: any) => ({
    name: `v${version.version}`,
    score: `${((version.accuracy || 0) * 100).toFixed(0)}% score`,
    changes: parseDiff(version.diff),
  }));
};

// 解析 diff 字符串为结构化变更数组
const parseDiff = (diff: string | null): { type: 'add' | 'remove'; text: string }[] => {
  if (!diff) return [];
  return diff.split('\n').map((line: string) => ({
    type: line.startsWith('+') ? 'add' : 'remove',
    text: line.replace(/^[+-]\s*/, ''),
  }));
};

export const usePromptVersions = () => {
  return useQuery<PromptVersion[], Error>({
    queryKey: ['prompt-versions'],
    queryFn: fetchPromptVersions,
  });
};
