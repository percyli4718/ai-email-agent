import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { API_BASE_URL, Email } from '../types/api';

const fetchEmails = async (limit?: number): Promise<Email[]> => {
  const url = limit ? `${API_BASE_URL}/emails?limit=${limit}` : `${API_BASE_URL}/emails`;
  const response = await fetch(url);
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

const fetchEmailsPaginated = async ({ pageParam = 1 }): Promise<{ emails: Email[]; nextPage: number | null }> => {
  const limit = 20; // 每页 20 条
  const response = await fetch(`${API_BASE_URL}/emails?limit=${limit}&offset=${(pageParam - 1) * limit}`);
  if (!response.ok) {
    throw new Error('获取邮件列表失败');
  }
  const data = await response.json();
  const emails = (data.emails || []).map((email: any) => ({
    ...email,
    from: email.from_address,
    time: new Date(email.received_at).toLocaleTimeString(),
    status: email.status === 'pending' ? 'new' : email.status === 'processing' ? 'processing' : 'done',
  }));

  return {
    emails,
    nextPage: emails.length === limit ? pageParam + 1 : null,
  };
};

export const useEmails = () => {
  return useQuery<Email[], Error>({
    queryKey: ['emails'],
    queryFn: () => fetchEmails(50), // 默认加载 50 条
  });
};

export const useEmailsInfinite = () => {
  return useInfiniteQuery({
    queryKey: ['emails-infinite'],
    queryFn: fetchEmailsPaginated,
    getNextPageParam: (lastPage) => lastPage.nextPage,
    initialPageParam: 1,
  });
};
