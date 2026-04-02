/**
 * 审批 API 服务
 */
import type { ApprovalRequest, ApprovalRequestCreate } from '../types/approval';

const API_BASE_URL = '/api';

/**
 * 获取审批请求列表
 */
export async function getApprovalRequests(status?: string, limit?: number): Promise<{ requests: ApprovalRequest[]; total: number }> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (limit) params.append('limit', limit.toString());

  const queryString = params.toString();
  const endpoint = queryString ? `/approvals?${queryString}` : '/approvals';

  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  if (!response.ok) {
    throw new Error('Failed to fetch approval requests');
  }
  return response.json();
}

/**
 * 获取单个审批请求详情
 */
export async function getApprovalRequest(id: number): Promise<ApprovalRequest> {
  const response = await fetch(`${API_BASE_URL}/approvals/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch approval request');
  }
  return response.json();
}

/**
 * 批准审批请求
 */
export async function approveApprovalRequest(
  id: number,
  reviewer: string,
  comments?: string
): Promise<{ success: boolean }> {
  const response = await fetch(`${API_BASE_URL}/approvals/${id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer, comments }),
  });
  if (!response.ok) {
    throw new Error('Failed to approve request');
  }
  return response.json();
}

/**
 * 拒绝审批请求
 */
export async function rejectApprovalRequest(
  id: number,
  reviewer: string,
  comments: string
): Promise<{ success: boolean }> {
  const response = await fetch(`${API_BASE_URL}/approvals/${id}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer, comments }),
  });
  if (!response.ok) {
    throw new Error('Failed to reject request');
  }
  return response.json();
}

/**
 * 创建审批请求
 */
export async function createApprovalRequest(
  data: ApprovalRequestCreate
): Promise<ApprovalRequest> {
  const response = await fetch(`${API_BASE_URL}/approvals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create approval request');
  }
  return response.json();
}
