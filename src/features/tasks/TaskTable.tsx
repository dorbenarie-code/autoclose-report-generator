import React from "react";
import { useTasks } from "./useTasks";

export function TaskTable() {
  const { tasks, loading, updateStatus } = useTasks();

  if (loading) return <div className="p-4">Loading tasks...</div>;

  return (
    <div className="overflow-x-auto p-4">
      <table className="w-full text-sm">
        <thead className="text-gray-500 border-b">
          <tr>
            <th className="text-left py-2">Title</th>
            <th>Status</th>
            <th>Created</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map(task => (
            <tr key={task.id} className="border-b hover:bg-gray-50">
              <td>{task.meta.title}</td>
              <td>{task.status}</td>
              <td>{new Date(task.timestamp).toLocaleString()}</td>
              <td>
                {task.status === "Open" ? (
                  <button
                    className="text-blue-600 hover:underline"
                    onClick={() => updateStatus(task.id, "Resolved")}
                  >
                    Resolve
                  </button>
                ) : (
                  <button
                    className="text-gray-600 hover:underline"
                    onClick={() => updateStatus(task.id, "Open")}
                  >
                    Reopen
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
