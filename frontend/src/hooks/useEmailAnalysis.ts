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
      title: 'Layer 1: 分类与路由',
      badge: '已完成',
      fields: [
        { label: '类型', value: data.layer1_classification.type },
        { label: '优先级', value: (data.layer1_classification.priority_score * 100).toFixed(0) + '%' },
        { label: '紧急程度', value: data.layer1_classification.urgency },
        { label: '语言', value: data.layer1_classification.language },
        { label: '区域', value: data.layer1_classification.customer_region },
        { label: '路由', value: data.layer1_classification.suggested_route },
        { label: '需要人工', value: data.layer1_classification.requires_human ? '是' : '否' },
        { label: '产品', value: data.layer1_classification.products_mentioned.join(', ') || '无' },
      ],
    });
  }

  // Layer 2: Retrieval
  if (data.layer2_retrieval) {
    sections.push({
      title: 'Layer 2: 向量检索',
      badge: '已完成',
      fields: [
        { label: '查询', value: data.layer2_retrieval.query.substring(0, 30) + '...' },
        { label: '检索时间', value: `${data.layer2_retrieval.retrieval_time_ms.toFixed(1)}ms` },
        { label: '结果数量', value: data.layer2_retrieval.results.length.toString() },
        { label: '最高相似度', value: data.layer2_retrieval.results[0]?.similarity ? (data.layer2_retrieval.results[0].similarity * 100).toFixed(0) + '%' : 'N/A' },
      ],
    });
  }

  // Layer 3: Structured Output
  if (data.layer3_output) {
    sections.push({
      title: 'Layer 3: 结构化输出',
      badge: '已完成',
      fields: [
        { label: '报价 ID', value: data.layer3_output.quote_id },
        { label: '总金额', value: `$${data.layer3_output.total_amount.toFixed(2)}` },
        { label: '有效期至', value: data.layer3_output.valid_until },
        { label: 'shipping 港口', value: data.layer3_output.shipping_port },
        { label: '付款条款', value: data.layer3_output.payment_terms },
        { label: '项目数量', value: data.layer3_output.items.length.toString() },
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
