import React, { useEffect, useState } from 'react';
import { getInsights, createTaskFromInsight, type Insight } from '../../lib/api';
import { Loader } from '../ui/loader';

interface InsightListProps {
  limit?: number;
  span?: number;
}

const InsightList: React.FC<InsightListProps> = ({ limit = 5 }) => {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Insight | null>(null);
  const [creatingTask, setCreatingTask] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getInsights(limit)
      .then(setInsights)
      .catch((err) => {
        if (err?.response?.status === 500) {
          setError('A server error occurred (500). Please try again later.');
        } else {
          setError('Failed to load insights. Please check your connection or try again.');
        }
        if ((import.meta as any).env.MODE !== 'production') {
          console.error('Insights fetch error:', err);
        }
      })
      .finally(() => setLoading(false));
  }, [limit]);

  const handleCreateTask = async (insight: Insight) => {
    setCreatingTask(true);
    try {
      await createTaskFromInsight(insight.id);
      setSelected(null);
    } catch {
      alert('Failed to create task.');
    } finally {
      setCreatingTask(false);
    }
  };

  if (loading) return <Loader />;
  if (error) return <div className="p-4 text-red-500">{error}</div>;
  if (!insights.length) return <div className="p-4 text-gray-400">No insights found.</div>;

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-3">Recent Insights</h3>
      <ul className="divide-y divide-gray-100">
        {insights.map((insight) => (
          <li
            key={insight.id}
            className={`py-3 px-2 cursor-pointer rounded transition flex flex-col gap-1 hover:bg-gray-50 ${
              insight.severity === 'critical'
                ? 'border-l-4 border-red-500 bg-red-50/30'
                : 'border-l-4 border-blue-400 bg-blue-50/20'
            } ${selected?.id === insight.id ? 'ring-2 ring-blue-400 bg-blue-100/40' : ''}`}
            onClick={() => setSelected(insight)}
            tabIndex={0}
            aria-label={`View details for ${insight.title}`}
          >
            <div className="flex items-center gap-2">
              <span
                className={`text-xs font-bold uppercase tracking-wide ${
                  insight.severity === 'critical'
                    ? 'text-red-600'
                    : 'text-blue-600'
                }`}
              >
                {insight.severity}
              </span>
              <span className="text-sm font-medium">{insight.title}</span>
              <span className="ml-auto text-xs text-gray-400">
                {new Date(insight.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            <div className="text-gray-600 text-sm truncate max-w-full">
              {insight.message}
            </div>
          </li>
        ))}
      </ul>
      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-6 relative">
            <button
              className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
              onClick={() => setSelected(null)}
              aria-label="Close"
            >
              &times;
            </button>
            <div className="mb-4">
              <span
                className={`inline-block px-2 py-1 text-xs rounded font-semibold mb-2 ${
                  selected.severity === 'critical'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-blue-100 text-blue-700'
                }`}
              >
                {selected.severity.toUpperCase()}
              </span>
              <h2 className="text-xl font-bold mb-1">{selected.title}</h2>
              <p className="text-gray-500 text-sm mb-2">
                {new Date(selected.createdAt).toLocaleString()}
              </p>
              <p className="text-gray-700 whitespace-pre-line">{selected.message}</p>
            </div>
            <div className="flex justify-end gap-2">
              <button
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
                onClick={() => handleCreateTask(selected)}
                disabled={creatingTask}
              >
                {creatingTask ? 'Creating...' : 'Create Task'}
              </button>
              <button
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300 transition"
                onClick={() => setSelected(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InsightList; 