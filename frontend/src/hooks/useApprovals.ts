/**
 * 审批请求 hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getApprovalRequests,
  getApprovalRequest,
  approveApprovalRequest,
  rejectApprovalRequest,
} from '../services/approvals';
import type { ApprovalRequest } from '../types/approval';

/**
 * 获取审批请求列表
 */
export const useApprovalRequests = (status?: string) => {
  return useQuery({
    queryKey: ['approvals', status],
    queryFn: () => getApprovalRequests(status),
  });
};

/**
 * 获取单个审批请求详情
 */
export const useApprovalRequest = (id: number | null) => {
  return useQuery<ApprovalRequest>({
    queryKey: ['approval', id],
    queryFn: () => getApprovalRequest(id!),
    enabled: !!id,
  });
};

/**
 * 批准审批请求
 */
export const useApproveApproval = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reviewer, comments }: { id: number; reviewer: string; comments?: string }) =>
      approveApprovalRequest(id, reviewer, comments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
    },
  });
};

/**
 * 拒绝审批请求
 */
export const useRejectApproval = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reviewer, comments }: { id: number; reviewer: string; comments: string }) =>
      rejectApprovalRequest(id, reviewer, comments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
    },
  });
};
