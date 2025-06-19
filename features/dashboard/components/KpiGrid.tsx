import React from 'react'
import { Loader } from '@/components/ui/loader'
import { KpiCard, KpiCardProps } from './KpiCard'

export type KpiColor = NonNullable<KpiCardProps['color']>

interface KpiConfig {
  key: keyof KpiResponse
  title: string
  color: KpiColor
}

export interface KpiResponse {
  total_revenue: number
  average_income: number
  total_reports: number
  crit_count: number
  open_tasks: number
  flag_rate: number
}

interface KpiGridProps {
  data?: KpiResponse | null
  loading?: boolean
  error?: string
  className?: string
}

const configs: KpiConfig[] = [
  { key: 'total_revenue', title: 'Total Revenue', color: 'green' },
  { key: 'average_income', title: 'Average Income', color: 'blue' },
  { key: 'total_reports', title: 'Total Reports', color: 'gray' },
  { key: 'crit_count', title: 'Critical Count', color: 'red' },
  { key: 'open_tasks', title: 'Open Tasks', color: 'gray' },
  { key: 'flag_rate', title: 'Flag Rate', color: 'red' },
]

export const KpiGrid: React.FC<KpiGridProps> = ({
  data,
  loading = false,
  error,
  className = '',
}) => {
  if (loading) {
    return (
      <div className={`col-span-12 flex items-center justify-center p-4 ${className}`}>
        <Loader />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className={`col-span-12 text-center text-red-500 p-4 ${className}`}>
        {error || 'Error loading KPI data.'}
      </div>
    )
  }

  return (
    <div
      className={`col-span-12 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 ${className}`}
    >
      {configs.map(({ key, title, color }) => (
        <KpiCard
          key={key}
          title={title}
          value={
            typeof data[key] === 'number'
              ? data[key].toLocaleString()
              : data[key]
          }
          color={color}
        />
      ))}
    </div>
  )
}
