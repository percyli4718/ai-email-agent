/**
 * 审批工作流类型定义
 */

export interface ApprovalRequest {
  id: number;
  email_id: string;
  requester: string;
  request_type: 'high_amount' | 'special_terms' | 'new_customer' | 'risk_control' | 'other';
  amount: number | null;
  currency: string;
  reason: string;
  details: Record<string, any> | null;
  status: 'pending' | 'approved' | 'rejected' | 'cancelled';
  reviewer: string | null;
  reviewed_at: string | null;
  comments: string | null;
  created_at: string;
}

export interface ApprovalRequestCreate {
  email_id: string;
  requester: string;
  request_type: string;
  reason: string;
  amount?: number;
  currency?: string;
  details?: Record<string, any>;
}

export interface ApprovalRequestResponse {
  requests: ApprovalRequest[];
  total: number;
}
