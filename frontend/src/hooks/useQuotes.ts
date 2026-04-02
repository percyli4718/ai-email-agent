/**
 * 报价单 hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getQuotes,
  getQuote,
  generateQuote,
  getEmailQuotes,
  updateQuoteStatus,
  deleteQuote,
} from '../services/quotes';
import type { QuoteFilterStatus } from '../types/quote';

/**
 * 获取报价列表
 */
export const useQuotes = (status?: QuoteFilterStatus) => {
  return useQuery({
    queryKey: ['quotes', status],
    queryFn: () => getQuotes(status),
  });
};

/**
 * 获取单个报价详情
 */
export const useQuote = (id: string | null) => {
  return useQuery({
    queryKey: ['quote', id],
    queryFn: () => getQuote(id!),
    enabled: !!id,
  });
};

/**
 * 获取邮件关联的报价
 */
export const useEmailQuotes = (emailId: string | null) => {
  return useQuery({
    queryKey: ['emailQuotes', emailId],
    queryFn: () => getEmailQuotes(emailId!),
    enabled: !!emailId,
  });
};

/**
 * 生成报价单
 */
export const useGenerateQuote = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (emailId: string) => generateQuote(emailId),
    onSuccess: (data, emailId) => {
      queryClient.invalidateQueries({ queryKey: ['quotes'] });
      queryClient.invalidateQueries({ queryKey: ['emailQuotes', emailId] });
      queryClient.invalidateQueries({ queryKey: ['quote', data.quote.quote_id] });
    },
  });
};

/**
 * 更新报价状态
 */
export const useUpdateQuoteStatus = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      updateQuoteStatus(id, status),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['quotes'] });
      queryClient.invalidateQueries({ queryKey: ['quote', id] });
    },
  });
};

/**
 * 删除报价单
 */
export const useDeleteQuote = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteQuote(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotes'] });
    },
  });
};
