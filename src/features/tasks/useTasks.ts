import { useEffect, useState } from "react";
import { getAllTasks, updateTaskStatus, Task } from "./api";

export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAllTasks().then(setTasks).finally(() => setLoading(false));
  }, []);

  const updateStatus = async (id: string, status: "Open" | "Resolved") => {
    await updateTaskStatus(id, status);
    setTasks(prev =>
      prev.map(task => (task.id === id ? { ...task, status } : task))
    );
  };

  return { tasks, loading, updateStatus };
}
