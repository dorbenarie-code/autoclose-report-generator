import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import LayoutShell from "./LayoutShell";
import ProtectedRoute from "./ProtectedRoute";
import { TaskTable } from "../features/tasks/TaskTable";

// Feature pages (dummy)
const DashboardPage = () => <div className="text-2xl font-bold">Dashboard Page</div>;
const ReportsPage = () => <div className="text-2xl font-bold">Reports Page</div>;
const InsightsPage = () => <div className="text-2xl font-bold">Insights Page</div>;
// const TasksPage = () => <div className="text-2xl font-bold">Tasks Page</div>;
const RulesPage = () => <div className="text-2xl font-bold">Finance Rules Page</div>;
const PermissionsPage = () => <div className="text-2xl font-bold">Permissions Page</div>;

const Router: React.FC = () => (
  <Routes>
    <Route element={<LayoutShell />}>
      <Route index element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route
        path="/reports"
        element={
          <ProtectedRoute roles={["admin", "manager", "finance"]}>
            <ReportsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/insights"
        element={
          <ProtectedRoute roles={["admin", "manager", "finance"]}>
            <InsightsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tasks"
        element={
          <ProtectedRoute roles={["admin", "manager"]}>
            <TaskTable />
          </ProtectedRoute>
        }
      />
      <Route
        path="/rules"
        element={
          <ProtectedRoute roles={["admin", "finance"]}>
            <RulesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/permissions"
        element={
          <ProtectedRoute roles={["admin"]}>
            <PermissionsPage />
          </ProtectedRoute>
        }
      />
    </Route>
  </Routes>
);

export default Router; 