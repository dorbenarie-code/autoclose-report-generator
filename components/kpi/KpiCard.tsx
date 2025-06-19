import React from 'react'
import { motion } from 'framer-motion'
import type { LucideIcon } from 'lucide-react'
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Users,
  CheckCircle
} from 'lucide-react'

export type KpiCardProps = {
  title: string
  value: string | number
  icon?: LucideIcon
  color?: 'blue' | 'green' | 'red' | 'gray'
  className?: string
}

const colorMap: Record<NonNullable<KpiCardProps['color']>, string> = {
  blue: 'bg-blue-100 text-blue-700',
  green: 'bg-green-100 text-green-700',
  red: 'bg-red-100 text-red-700',
  gray: 'bg-gray-100 text-gray-700'
}

const iconMap: Record<string, LucideIcon> = {
  revenue: DollarSign,
  orders: TrendingUp,
  success: CheckCircle,
  techs: Users,
  decline: TrendingDown
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  icon,
  color = 'gray',
  className = ''
}) => {
  // Determine icon: prop override → map by title key → default Users
  const key = title.toLowerCase().replace(/\s+/g, '_')
  const IconComponent: LucideIcon = icon || iconMap[key] || Users

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.03 }}
      transition={{ duration: 0.3 }}
      className={`flex flex-col justify-between p-4 rounded-2xl shadow-md hover:shadow-lg transition-shadow w-full sm:w-1/2 md:w-1/3 lg:w-1/4 bg-white ${className}`}
    >
      <div>
        <span className="block text-sm font-medium text-gray-500">{title}</span>
        <span className="mt-1 text-2xl font-bold leading-tight">{value}</span>
      </div>
      <div
        className={`mt-4 inline-flex items-center justify-center w-10 h-10 rounded-full ${colorMap[color]}`}
      >
        <IconComponent className="w-5 h-5" />
      </div>
    </motion.div>
  )
}
