import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // include cookies/auth if needed
  timeout: 10_000,       // 10s timeout for safety
});

export type Insight = {
  id: string;
  title: string;
  message: string;
  severity: "critical" | "warning" | "info";
  createdAt: string; // ISO string
  meta?: Record<string, any>;
};

export type KpiResponse = {
  total_revenue: number;
  average_income: number;
  total_reports: number;
  crit_count: number;
  open_tasks: number;
  flag_rate: number;
};

export type IncomePoint = {
  date: string;
  amount: number;
};

/**
 * Fetch KPI metrics from the backend.
 */
export async function getKpiData(): Promise<KpiResponse> {
  try {
    const response = await api.get<KpiResponse>("/kpi/summary");
    return response.data;
  } catch (error) {
    console.error('Failed to fetch KPI data:', error);
    throw new Error(`Failed to fetch KPI data: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/** Fetches the daily income trend */
export async function getIncomeTrend(from?: string, to?: string): Promise<IncomePoint[]> {
  const response = await api.get<IncomePoint[]>("/kpi/income_trend", {
    params: { from, to },
  })
  return response.data
}

/**
 * Fetches the latest insights from the backend.
 */
export async function getInsights(limit: number): Promise<Insight[]> {
  try {
    const response = await api.get<Insight[]>(`/insights?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch insights:', error);
    throw new Error(`Failed to fetch insights: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Creates a task from an insight by ID.
 */
export async function createTaskFromInsight(insightId: string): Promise<void> {
  try {
    await api.post("/tasks", { insightId });
  } catch (error) {
    console.error('Failed to create task from insight:', error);
    throw new Error(`Failed to create task from insight: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
} 