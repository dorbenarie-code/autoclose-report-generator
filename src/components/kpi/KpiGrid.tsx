import React from 'react';
import { KpiCard } from '../../features/dashboard/KpiCard';
import { Loader } from '../ui/loader';

export interface KpiResponse {
  total_revenue: number;
  average_income: number;
  total_reports: number;
  crit_count: number;
  open_tasks: number;
  flag_rate: number;
}

const kpiConfigs = [
  { title: 'Total Revenue', key: 'total_revenue', color: 'success' },
  { title: 'Average Income', key: 'average_income', color: 'primary' },
  { title: 'Total Reports', key: 'total_reports', color: 'primary' },
  { title: 'Critical Alerts', key: 'crit_count', color: 'critical' },
  { title: 'Open Tasks', key: 'open_tasks', color: 'primary' },
  { title: '% with Flags', key: 'flag_rate', color: 'primary' }
] as const;

interface KpiGridProps {
  data: KpiResponse | null;
  loading: boolean;
  error: string;
}

const formatValue = (key: string, value: number) => {
  if (key === 'flag_rate') return `${value.toFixed(1)}%`;
  if (key === 'total_revenue' || key === 'average_income') return `$${value.toLocaleString()}`;
  return value.toLocaleString();
};

export function KpiGrid({ data, loading, error }: KpiGridProps) {
  if (loading) return <Loader />;
  if (error) return <div className="p-4 text-center text-red-500">{error}</div>;
  if (!data) return <div className="p-4 text-center text-red-500">No data available.</div>;

  return (
    <>
      {kpiConfigs.map(config => (
        <KpiCard
          key={config.key}
          title={config.title}
          value={formatValue(config.key, data[config.key as keyof KpiResponse] as number)}
          color={config.color as "primary" | "critical" | "success"}
          span={3}
        />
      ))}
    </>
  );
} 