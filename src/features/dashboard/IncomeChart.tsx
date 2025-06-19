// src/features/dashboard/IncomeChart.tsx

import React, { useEffect, useState, useMemo } from "react";
import ReactECharts from "echarts-for-react";
import { getIncomeTrend } from "@/lib/api";
import { Loader } from "@/components/ui/loader";

export interface IncomePoint {
  /** Date in ISO format (YYYY-MM-DD) */
  date: string;
  /** Total income for that day */
  amount: number;
}

interface IncomeChartProps {
  /** Number of grid columns to span (1–12) */
  span?: number;
}

export const IncomeChart: React.FC<IncomeChartProps> = ({ span = 8 }) => {
  const [data, setData] = useState<IncomePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch daily income trend from the backend
  useEffect(() => {
    async function fetchTrend() {
      try {
        const trend = await getIncomeTrend();
        setData(trend);
      } catch (err) {
        console.error("Failed to load income trend:", err);
        setError("Unable to load income data.");
      } finally {
        setLoading(false);
      }
    }
    fetchTrend();
  }, []);

  // Build chart options, memoized for performance
  const option = useMemo(() => ({
    tooltip: {
      trigger: "axis",
      formatter: (params: any) => {
        const { name, value } = params[0];
        return `${name}: $${value}`;
      },
    },
    xAxis: {
      type: "category",
      data: data.map((pt) => pt.date),
      axisLabel: {
        rotate: 45,
        fontSize: 10,
        interval: Math.ceil(data.length / 7), // show ~7 labels max
      },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: "${value}",
      },
    },
    series: [
      {
        name: "Income",
        type: "bar",       // or "line" if preferred
        data: data.map((pt) => pt.amount),
        smooth: true,
        animationDuration: 800,
        animationEasing: "cubicOut",
        itemStyle: {
          color: "#2563EB", // primary blue
        },
      },
    ],
    grid: {
      left: "3%",
      right: "3%",
      bottom: "20%",
      containLabel: true,
    },
  }), [data]);

  // Loading state
  if (loading) {
    return (
      <div style={{ gridColumn: `span ${span}` }}>
        <Loader />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div
        style={{ gridColumn: `span ${span}` }}
        className="p-4 text-center text-red-500"
      >
        {error}
      </div>
    );
  }

  // Main render
  return (
    <div style={{ gridColumn: `span ${span}` }}>
      <div className="bg-white dark:bg-gray-900 rounded-xl p-4 shadow-sm h-full flex flex-col">
        <h2 className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-4">
          Daily Income
        </h2>
        <div className="flex-1">
          <ReactECharts
            option={option}
            style={{ width: "100%", height: "100%" }}
          />
        </div>
      </div>
    </div>
  );
};
