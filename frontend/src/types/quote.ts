/**
 * 报价单相关类型定义
 */

/** 报价项目 */
export interface QuoteItem {
  product_name: string;
  specification: string;
  quantity: number;
  unit: string;
  unit_price: number;
  amount: number;
}

/** 报价单 */
export interface Quote {
  quote_id: string;
  email_id: string;
  customer_name: string;
  customer_email: string;
  company: string;
  total_amount: number;
  currency: string;
  items: QuoteItem[];
  shipping_port: string;
  payment_terms: string;
  delivery_time: string;
  valid_until: string;
  notes?: string | null;
  status: 'draft' | 'pending' | 'sent' | 'accepted' | 'rejected' | 'expired';
  created_at: string;
  updated_at: string;
}

/** 报价单创建请求 */
export interface QuoteCreate {
  email_id: string;
  customer_name: string;
  customer_email: string;
  company: string;
  items: QuoteItem[];
  shipping_port: string;
  payment_terms: string;
  delivery_time: string;
  valid_until: string;
  notes?: string | null;
}

/** 报价单生成请求 */
export interface QuoteGenerateRequest {
  email_id: string;
}

/** 报价单生成响应 */
export interface QuoteGenerateResponse {
  quote: Quote;
  message: string;
}

/** 报价列表响应 */
export interface QuoteListResponse {
  quotes: Quote[];
  total: number;
}

/** 报价状态过滤 */
export type QuoteFilterStatus = 'all' | 'draft' | 'pending' | 'sent' | 'accepted' | 'rejected' | 'expired';
