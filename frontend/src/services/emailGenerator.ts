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
