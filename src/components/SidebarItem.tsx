import React from "react";
import { NavLink } from "react-router-dom";

interface SidebarItemProps {
  to: string;
  label: string;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  hide?: boolean;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ to, label, icon, badge, hide }) => {
  if (hide) return null;
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-2 px-4 py-2 rounded transition-colors font-medium
        ${isActive ? "bg-primary/10 text-primary" : "text-gray-base hover:bg-gray-100 dark:hover:bg-gray-800"}`
      }
      end
    >
      {icon}
      <span>{label}</span>
      {badge && <span className="ml-auto">{badge}</span>}
    </NavLink>
  );
};

export default SidebarItem; 