import React from "react";
import { Navigate } from "react-router-dom";
import { useUser } from "./UserContext";

interface ProtectedRouteProps {
  roles: string[];
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ roles, children }) => {
  const { role } = useUser();

  if (!roles.includes(role)) {
    return (
      <div className="p-6 text-red-600 font-semibold">
        🚫 Access denied – this page is restricted for your role.
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute; 