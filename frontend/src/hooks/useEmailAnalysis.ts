import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL, AnalysisSection } from '../types/api';

const fetchEmailAnalysis = async (emailId: string): Promise<AnalysisSection[]> => {
  const response = await fetch(`${API_BASE_URL}/emails/${emailId}/analysis`);
  if (!response.ok) {
    throw new Error('获取邮件分析失败');
  }
  const data = await response.json();
  // 后端返回 { email_id, layer1_classification, layer2_retrieval, layer3_output }
  // 前端期望 AnalysisSection[] 格式
  const sections: AnalysisSection[] = [];

  // Layer 1: Classification
  if (data.layer1_classification) {
    sections.push({
      title: 'Layer 1: Classification & Routing',
      badge: 'Completed',
      fields: [
        { label: 'Type', value: data.layer1_classification.type },
        { label: 'Priority', value: (data.layer1_classification.priority_score * 100).toFixed(0) + '%' },
        { label: 'Urgency', value: data.layer1_classification.urgency },
        { label: 'Language', value: data.layer1_classification.language },
        { label: 'Region', value: data.layer1_classification.customer_region },
        { label: 'Route', value: data.layer1_classification.suggested_route },
        { label: 'Human Required', value: data.layer1_classification.requires_human ? 'Yes' : 'No' },
        { label: 'Products', value: data.layer1_classification.products_mentioned.join(', ') || 'None' },
      ],
    });
  }

  // Layer 2: Retrieval
  if (data.layer2_retrieval) {
    sections.push({
      title: 'Layer 2: Vector Retrieval',
      badge: 'Completed',
      fields: [
        { label: 'Query', value: data.layer2_retrieval.query.substring(0, 30) + '...' },
        { label: 'Retrieval Time', value: `${data.layer2_retrieval.retrieval_time_ms.toFixed(1)}ms` },
        { label: 'Results Count', value: data.layer2_retrieval.results.length.toString() },
        { label: 'Top Similarity', value: data.layer2_retrieval.results[0]?.similarity ? (data.layer2_retrieval.results[0].similarity * 100).toFixed(0) + '%' : 'N/A' },
      ],
    });
  }

  // Layer 3: Structured Output
  if (data.layer3_output) {
    sections.push({
      title: 'Layer 3: Structured Output',
      badge: 'Completed',
      fields: [
        { label: 'Quote ID', value: data.layer3_output.quote_id },
        { label: 'Total Amount', value: `$${data.layer3_output.total_amount.toFixed(2)}` },
        { label: 'Valid Until', value: data.layer3_output.valid_until },
        { label: 'Shipping Port', value: data.layer3_output.shipping_port },
        { label: 'Payment Terms', value: data.layer3_output.payment_terms },
        { label: 'Items Count', value: data.layer3_output.items.length.toString() },
      ],
    });
  }

  return sections;
};

export const useEmailAnalysis = (emailId: string | null) => {
  return useQuery<AnalysisSection[], Error>({
    queryKey: ['analysis', emailId],
    queryFn: () => fetchEmailAnalysis(emailId!),
    enabled: !!emailId,
  });
};
