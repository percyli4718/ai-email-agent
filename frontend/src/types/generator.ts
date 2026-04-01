// 邮件生成请求
export interface GenerateEmailsRequest {
  count: number;
  auto_process: boolean;
  filters?: {
    type?: string;
    region?: string;
  };
}

// 生成的客户信息
export interface GeneratedCustomer {
  name: string;
  company: string;
  email: string;
}

// 生成的邮件
export interface GeneratedEmail {
  id: string;
  from_address: string;
  subject: string;
  preview: string;
  priority: 'low' | 'medium' | 'high';
  status: string;
  region: string;
  customer: GeneratedCustomer;
}

// 邮件生成响应
export interface GenerateEmailsResponse {
  generated_emails: GeneratedEmail[];
  total: number;
  auto_process_started: boolean;
}

// 模板响应
export interface EmailTemplate {
  id: number;
  type: string;
  product_name: string;
  region: string;
  quantity_range: string;
  is_active: boolean;
  created_at: string;
}

// 模板列表响应
export interface EmailTemplatesResponse {
  templates: EmailTemplate[];
  total: number;
}
