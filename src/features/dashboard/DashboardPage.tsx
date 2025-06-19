import React, { useEffect, useState } from "react";
import { Grid } from "../../components/ui/grid";
import InsightList from "../../components/insights/InsightList";
import { getKpiData } from "../../lib/api";
import { KpiGrid, KpiResponse } from "../../components/kpi/KpiGrid";
import { IncomeChartBlock } from "@/components/charts/IncomeChartBlock";

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KpiResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const fetchKPIs = async () => {
      try {
        const data = await getKpiData();
        setKpis(data);
      } catch (err) {
        console.error('❌ Failed to load KPI data', err);
        setError('Failed to load KPI data.');
      } finally {
        setLoading(false);
      }
    };
    fetchKPIs();
  }, []);

  return (
    <Grid cols={12} gap={4}>
      <KpiGrid data={kpis} loading={loading} error={error} />
      <IncomeChartBlock />
      <div className="col-span-12 md:col-span-6">
        <InsightList limit={5} span={6} />
      </div>
    </Grid>
  );
} 