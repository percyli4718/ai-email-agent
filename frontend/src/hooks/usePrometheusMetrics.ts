/**
 * Prometheus Metrics Hook
 *
 * 用于获取 Prometheus 格式的指标数据
 */
import { useState, useEffect } from 'react';

interface PrometheusMetrics {
  counters: Record<string, number>;
  gauges: Record<string, number>;
  histograms: Record<string, {
    count: number;
    sum: number;
    avg: number;
    min: number;
    max: number;
    p50: number;
    p95: number;
  }>;
}

export function usePrometheusMetrics() {
  const [data, setData] = useState<PrometheusMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchMetrics = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/metrics/prometheus');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const text = await response.text();

      // 解析 Prometheus 格式
      const parsed: PrometheusMetrics = {
        counters: {},
        gauges: {},
        histograms: {}
      };

      const lines = text.split('\n');
      let currentType: 'counter' | 'gauge' | 'histogram' | null = null;
      let currentMetric: string | null = null;

      for (const line of lines) {
        if (line.startsWith('# TYPE')) {
          const parts = line.split(' ');
          currentMetric = parts[2];
          currentType = parts[3] as 'counter' | 'gauge' | 'histogram';
        } else if (line && !line.startsWith('#')) {
          const parts = line.split(' ');
          const name = parts[0];
          const value = parseFloat(parts[1]);

          if (currentType === 'counter' && currentMetric) {
            parsed.counters[currentMetric] = value;
          } else if (currentType === 'gauge' && currentMetric) {
            parsed.gauges[currentMetric] = value;
          } else if (currentType === 'histogram' && currentMetric) {
            if (!parsed.histograms[currentMetric]) {
              parsed.histograms[currentMetric] = {
                count: 0,
                sum: 0,
                avg: 0,
                min: 0,
                max: 0,
                p50: 0,
                p95: 0
              };
            }
            if (name.endsWith('_count')) {
              parsed.histograms[currentMetric].count = value;
            } else if (name.endsWith('_sum')) {
              parsed.histograms[currentMetric].sum = value;
            } else if (name.endsWith('_avg')) {
              parsed.histograms[currentMetric].avg = value;
            } else if (name.endsWith('_min')) {
              parsed.histograms[currentMetric].min = value;
            } else if (name.endsWith('_max')) {
              parsed.histograms[currentMetric].max = value;
            } else if (name.endsWith('_p50')) {
              parsed.histograms[currentMetric].p50 = value;
            } else if (name.endsWith('_p95')) {
              parsed.histograms[currentMetric].p95 = value;
            }
          }
        }
      }

      setData(parsed);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  return { data, isLoading, error, refetch: fetchMetrics };
}
