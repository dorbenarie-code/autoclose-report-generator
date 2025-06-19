// src/components/charts/IncomeChartBlock.tsx

import React, { useEffect, useState } from "react"
import ReactECharts from "echarts-for-react"
import { getIncomeTrend } from "@/lib/api"
import { Card } from "@/components/ui/card"
import { DateRangePicker } from "@/components/ui/date-range-picker"
import { Button } from "@/components/ui/button"
import { Download } from "lucide-react"

export interface IncomePoint {
  date: string
  amount: number
}

interface DateRange {
  from: Date
  to: Date
}

export const IncomeChartBlock: React.FC = () => {
  const [data, setData] = useState<IncomePoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dateRange, setDateRange] = useState<DateRange>({
    from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 ימים אחורה
    to: new Date()
  })

  useEffect(() => {
    async function fetchTrend() {
      try {
        setLoading(true)
        const trend = await getIncomeTrend(
          dateRange.from.toISOString(),
          dateRange.to.toISOString()
        )
        setData(trend)
      } catch (err) {
        console.error("שגיאה בטעינת נתוני הכנסה:", err)
        setError("לא ניתן לטעון נתוני הכנסה")
      } finally {
        setLoading(false)
      }
    }
    fetchTrend()
  }, [dateRange])

  const option = {
    tooltip: {
      trigger: "axis",
      formatter: (params: any) => {
        const { name, value } = params[0]
        return `${name}: ₪${value.toLocaleString()}`
      },
    },
    xAxis: {
      type: "category",
      data: data.map((pt: IncomePoint) => pt.date),
      axisLabel: {
        rotate: 45,
        fontSize: 10,
        interval: Math.ceil(data.length / 7),
      },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: "₪{value}",
      },
    },
    series: [
      {
        name: "הכנסה",
        type: "bar",
        data: data.map((pt: IncomePoint) => pt.amount),
        smooth: true,
        animationDuration: 800,
        animationEasing: "cubicOut",
        itemStyle: {
          color: "#2563EB",
        },
      },
    ],
    grid: {
      left: "3%",
      right: "3%",
      bottom: "20%",
      containLabel: true,
    },
  }

  const handleExport = () => {
    const chart = document.querySelector('.echarts-for-react')
    if (chart) {
      const canvas = chart.querySelector('canvas')
      if (canvas) {
        const link = document.createElement('a')
        link.download = `income-chart-${new Date().toISOString().split('T')[0]}.png`
        link.href = canvas.toDataURL('image/png')
        link.click()
      }
    }
  }

  if (loading) {
    return (
      <Card className="col-span-12 p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="h-[300px] bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="col-span-12 p-4 text-center text-red-500">
        {error}
      </Card>
    )
  }

  return (
    <Card className="col-span-12 p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">
          מגמת הכנסות
        </h2>
        <div className="flex items-center gap-2">
          <DateRangePicker
            value={dateRange}
            onChange={setDateRange}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            className="flex items-center gap-1"
          >
            <Download className="w-4 h-4" />
            ייצוא
          </Button>
        </div>
      </div>
      <div className="h-[400px]">
        <ReactECharts
          option={option}
          style={{ width: "100%", height: "100%" }}
        />
      </div>
    </Card>
  )
}
