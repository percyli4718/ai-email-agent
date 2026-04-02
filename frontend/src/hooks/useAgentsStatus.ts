import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL, Agent } from '../types/api';

const fetchAgentsStatus = async (): Promise<Agent[]> => {
  const response = await fetch(`${API_BASE_URL}/agents/status`);
  if (!response.ok) {
    throw new Error('获取 Agent 状态失败');
  }
  const data = await response.json();
  // 后端返回 { ceo_agent_status, sub_agents, ... }，提取 sub_agents 并映射字段
  return (data.sub_agents || []).map((agent: any) => ({
    name: agent.agent_name,
    status: agent.status.charAt(0).toUpperCase() + agent.status.slice(1), // 'running' -> 'Running'
    budget: agent.actual_cost,
    budgetMax: agent.budget_allocated,
    description: undefined,
  }));
};

export const useAgentsStatus = () => {
  return useQuery<Agent[], Error>({
    queryKey: ['agents-status'],
    queryFn: fetchAgentsStatus,
    refetchInterval: 5000, // 5 秒轮询
  });
};
