/**
 * Workflow Hook
 *
 * 用于获取和管理邮件工作流状态的 React Hook
 */
import { useState, useEffect, useCallback } from 'react';
import { getEmailWorkflow, transitionWorkflowState, type WorkflowResponse } from '../services/api';

// ============================================================================
// Types
// ============================================================================

export interface UseWorkflowResult {
  workflow: WorkflowResponse | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  transitionState: (newState: string, triggeredBy: string, reason?: string, metadata?: Record<string, unknown>) => Promise<void>;
}

// ============================================================================
// Hook
// ============================================================================

/**
 * 工作流 Hook
 *
 * @param emailId 邮件 ID
 * @returns 工作流状态和管理函数
 */
export function useWorkflow(emailId: string | null): UseWorkflowResult {
  const [workflow, setWorkflow] = useState<WorkflowResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // 获取工作流数据
  const fetchWorkflow = useCallback(async () => {
    if (!emailId) {
      setWorkflow(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await getEmailWorkflow(emailId);
      setWorkflow(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch workflow'));
      console.error('Failed to fetch workflow:', err);
    } finally {
      setLoading(false);
    }
  }, [emailId]);

  // 状态转换
  const transitionState = useCallback(
    async (
      newState: string,
      triggeredBy: string,
      reason?: string,
      metadata?: Record<string, unknown>
    ) => {
      if (!emailId) return;

      try {
        const result = await transitionWorkflowState(
          emailId,
          newState,
          triggeredBy,
          reason,
          metadata
        );
        setWorkflow(result.workflow);
      } catch (err) {
        console.error('Failed to transition workflow state:', err);
        throw err;
      }
    },
    [emailId]
  );

  // 当 emailId 变化时重新获取数据
  useEffect(() => {
    fetchWorkflow();
  }, [fetchWorkflow]);

  return {
    workflow,
    loading,
    error,
    refetch: fetchWorkflow,
    transitionState,
  };
}

export default useWorkflow;
