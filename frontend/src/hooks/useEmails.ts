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

const fetchEmailsPaginated = async ({ pageParam = 1 }): Promise<{ emails: Email[]; nextPage: number | null; total: number }> => {
  const limit = 20; // 每页 20 条
  const offset = (pageParam - 1) * limit;
  const response = await fetch(`${API_BASE_URL}/emails?limit=${limit}&offset=${offset}`);
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

  const total = data.total || emails.length;
  const hasMore = offset + emails.length < total;

  return {
    emails,
    nextPage: hasMore ? pageParam + 1 : null,
    total,
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
