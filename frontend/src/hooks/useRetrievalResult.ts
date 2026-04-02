/**
 * Hook for fetching Layer 2 retrieval results
 *
 * 功能:
 * - 获取检索到的相似邮件
 * - 获取定价政策
 * - 获取合规要求
 */
import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL } from '../types/api';

// ============================================================================
// Types
// ============================================================================

export interface SimilarEmail {
  id: string;
  content: string;
  similarity: number;
  metadata: {
    region?: string;
    type?: string;
    date?: string;
  };
}

export interface PricingPolicy {
  product: string;
  base_price: number;
  discount_rate: number;
  currency: string;
}

export interface ComplianceRequirement {
  type: string;
  name: string;
  mandatory: boolean;
  description?: string;
}

export interface RetrievalResult {
  similar_emails: {
    documents: string[];
    metadatas: Record<string, any>[];
    distances?: number[];
    ids?: string[];
  };
  customer_history: {
    name?: string;
    tier?: string;
    region?: string;
  } | null;
  pricing_policy: {
    policies: PricingPolicy[];
    region: string;
  };
  compliance: {
    requirements: ComplianceRequirement[];
    region: string;
  };
}

// ============================================================================
// API Functions
// ============================================================================

const fetchRetrievalResult = async (emailId: string): Promise<RetrievalResult> => {
  const response = await fetch(`${API_BASE_URL}/emails/${emailId}/retrieval`);
  if (!response.ok) {
    throw new Error('获取检索结果失败');
  }
  return response.json();
};

// ============================================================================
// Hook Export
// ============================================================================

export const useRetrievalResult = (emailId: string | null) => {
  return useQuery<RetrievalResult, Error>({
    queryKey: ['retrieval', emailId],
    queryFn: () => fetchRetrievalResult(emailId!),
    enabled: !!emailId,
  });
};
