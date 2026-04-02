/**
 * 报价 API 服务
 */
import type {
  Quote,
  QuoteListResponse,
  QuoteGenerateRequest,
  QuoteGenerateResponse,
  QuoteFilterStatus,
} from '../types/quote';

const API_BASE_URL = '/api';

/**
 * 获取报价列表
 */
export async function getQuotes(status?: QuoteFilterStatus, limit?: number): Promise<QuoteListResponse> {
  const params = new URLSearchParams();
  if (status && status !== 'all') params.append('status', status);
  if (limit) params.append('limit', limit.toString());

  const queryString = params.toString();
  const endpoint = queryString ? `/quotes?${queryString}` : '/quotes';

  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  if (!response.ok) {
    throw new Error('Failed to fetch quotes');
  }
  return response.json();
}

/**
 * 获取单个报价详情
 */
export async function getQuote(id: string): Promise<Quote> {
  const response = await fetch(`${API_BASE_URL}/quotes/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch quote');
  }
  return response.json();
}

/**
 * 生成报价单
 */
export async function generateQuote(
  emailId: string
): Promise<QuoteGenerateResponse> {
  const response = await fetch(`${API_BASE_URL}/quotes/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email_id: emailId } as QuoteGenerateRequest),
  });
  if (!response.ok) {
    throw new Error('Failed to generate quote');
  }
  return response.json();
}

/**
 * 获取邮件关联的报价
 */
export async function getEmailQuotes(emailId: string): Promise<Quote[]> {
  const response = await fetch(`${API_BASE_URL}/emails/${emailId}/quotes`);
  if (!response.ok) {
    throw new Error('Failed to fetch email quotes');
  }
  const data = await response.json();
  return data.quotes || [];
}

/**
 * 更新报价状态
 */
export async function updateQuoteStatus(
  id: string,
  status: string
): Promise<{ message: string; quote_id: string }> {
  const response = await fetch(`${API_BASE_URL}/quotes/${id}/status?status=${status}`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to update quote status');
  }
  return response.json();
}

/**
 * 删除报价单
 */
export async function deleteQuote(id: string): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/quotes/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete quote');
  }
  return response.json();
}
