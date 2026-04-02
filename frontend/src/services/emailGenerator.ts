import type {
  GenerateEmailsRequest,
  GenerateEmailsResponse,
  EmailTemplatesResponse,
  GeneratedEmail,
} from '../types/generator';

const API_BASE_URL = '/api';

export async function generateEmails(
  request: GenerateEmailsRequest
): Promise<GenerateEmailsResponse> {
  const response = await fetch(`${API_BASE_URL}/emails/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '生成失败' }));
    throw new Error(error.detail || '生成邮件失败');
  }

  return response.json();
}

export async function getEmailTemplates(): Promise<EmailTemplatesResponse> {
  const response = await fetch(`${API_BASE_URL}/emails/templates`);

  if (!response.ok) {
    throw new Error('获取模板列表失败');
  }

  return response.json();
}

export async function generateSingleEmail(
  autoProcess: boolean = false
): Promise<GeneratedEmail> {
  const response = await generateEmails({
    count: 1,
    auto_process: autoProcess,
  });

  return response.generated_emails[0];
}

export async function updateTemplate(
  templateId: number,
  data: {
    subject_template?: string;
    body_template?: string;
    is_active?: boolean;
  }
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/emails/templates/${templateId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '更新失败' }));
    throw new Error(error.detail || '更新模板失败');
  }
}

export async function createTemplate(
  data: {
    type: string;
    product_name: string;
    region: string;
    quantity_range: string;
    subject_template: string;
    body_template: string;
  }
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/emails/templates`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '创建失败' }));
    throw new Error(error.detail || '创建模板失败');
  }
}

export async function deleteTemplate(templateId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/emails/templates/${templateId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '删除失败' }));
    throw new Error(error.detail || '删除模板失败');
  }
}
