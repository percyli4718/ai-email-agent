import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL, Email } from '../types/api';

const fetchEmails = async (): Promise<Email[]> => {
  const response = await fetch(`${API_BASE_URL}/api/emails`);
  if (!response.ok) {
    throw new Error('获取邮件列表失败');
  }
  const data = await response.json();
  // 映射后端字段到前端字段
  return (data.emails || []).map((email: any) => ({
    ...email,
    from: email.from_address,
    time: new Date(email.received_at).toLocaleTimeString(),
    // 状态映射：pending -> new, processing -> processing, completed -> done
    status: email.status === 'pending' ? 'new' : email.status === 'processing' ? 'processing' : 'done',
  }));
};

export const useEmails = () => {
  return useQuery<Email[], Error>({
    queryKey: ['emails'],
    queryFn: fetchEmails,
  });
};
