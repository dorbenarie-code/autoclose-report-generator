import React from "react";
import { useTheme } from "../app/ThemeProvider";
import { useUser } from "../app/UserContext";

const Topbar: React.FC = () => {
  const { theme, toggle } = useTheme();
  const { role } = useUser();

  const today = new Date().toLocaleDateString();

  return (
    <header className="h-16 flex items-center justify-between px-6 border-b bg-white dark:bg-gray-900">
      <div className="font-semibold text-gray-700 dark:text-gray-100">
        Welcome, <span className="capitalize">{role}</span> — {today}
      </div>
      <button
        onClick={toggle}
        className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-700 text-sm"
      >
        {theme === "dark" ? "🌙 Dark" : "☀️ Light"}
      </button>
    </header>
  );
};

export default Topbar; 