/**
 * 邮件详情 Hook
 *
 * 功能：获取单封邮件的完整详情
 */
import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL } from '../types/api';

export interface EmailDetail {
  id: string;
  subject: string;
  from_address: string;
  to_address?: string;
  cc_address?: string;
  body: string;
  raw_content?: string; // 后端返回的字段
  preview: string;
  received_at: string;
  status: string;
  region?: string;
}

const fetchEmailDetail = async (emailId: string): Promise<EmailDetail> => {
  const response = await fetch(`${API_BASE_URL}/emails/${emailId}`);
  if (!response.ok) {
    throw new Error('获取邮件详情失败');
  }
  return response.json();
};

export const useEmailDetail = (emailId: string | null) => {
  return useQuery<EmailDetail, Error>({
    queryKey: ['email-detail', emailId],
    queryFn: () => fetchEmailDetail(emailId!),
    enabled: !!emailId,
  });
};
