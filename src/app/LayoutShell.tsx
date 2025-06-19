import React from "react";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import { Outlet } from "react-router-dom";

const LayoutShell: React.FC = () => {
  return (
    <div className="flex h-screen bg-gray-bg text-gray-base">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Topbar />
        <main className="flex-1 p-6 overflow-y-auto bg-gray-bg">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default LayoutShell; 