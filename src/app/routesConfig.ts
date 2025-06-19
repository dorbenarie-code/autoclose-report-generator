import { lazy } from "react"

export const routes = [
  {
    path: "/dashboard",
    name: "Dashboard",
    element: lazy(() => import("@/features/dashboard/DashboardPage")),
    protected: true,
    roles: ["admin", "manager"],
  },
  {
    path: "/reports",
    name: "Reports",
    element: lazy(() => import("@/features/reports/ReportsPage")),
    protected: true,
  },
  {
    path: "/insights",
    name: "Insights",
    element: lazy(() => import("@/features/insights/InsightsPage")),
    protected: true,
  },
] 