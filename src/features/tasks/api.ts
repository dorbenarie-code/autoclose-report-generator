import { api } from "@/lib/api";

export type Task = {
  id: string;
  message: string;
  status: "Open" | "Resolved";
  timestamp: string;
  meta: {
    title: string;
    createdAt: string;
  };
};

export async function getAllTasks(): Promise<Task[]> {
  const res = await api.get("/tasks");
  return res.data;
}

export async function updateTaskStatus(id: string, status: "Open" | "Resolved") {
  const res = await api.put(`/tasks/${id}`, { status });
  return res.data;
}
