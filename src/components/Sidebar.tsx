import React from "react";
import { NavLink } from "react-router-dom";
import { useUser } from "../app/UserContext";
import {
  HiOutlineViewGrid, HiOutlineDocumentText, HiOutlineLightBulb,
  HiOutlineClipboardList, HiOutlineCurrencyDollar, HiOutlineUserGroup, HiMenu
} from "react-icons/hi";

const navItems = [
  { to: "/dashboard", label: "Overview" },
  { to: "/reports", label: "Reports" },
  { to: "/insights", label: "Insights" },
  { to: "/tasks", label: "Tasks" },
  { to: "/rules", label: "Rules", roles: ["admin", "finance"] },
  { to: "/permissions", label: "Permissions", roles: ["admin"] },
];

const Sidebar: React.FC = () => {
  const { role } = useUser();

  const visibleItems = navItems.filter(i => !i.roles || i.roles.includes(role));

  return (
    <aside className="w-56 bg-white dark:bg-gray-800 border-r h-full flex flex-col py-6">
      <div className="px-6 text-xl font-bold mb-8 text-primary">AutoClose</div>
      <nav className="flex-1 flex flex-col gap-1">
        {visibleItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `px-6 py-2 rounded text-base font-medium hover:bg-primary/10 ${
                isActive ? "bg-primary/10 text-primary" : "text-gray-base dark:text-white"
              }`
            }
            end
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar; 