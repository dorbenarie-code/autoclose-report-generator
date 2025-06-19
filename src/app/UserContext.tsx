import React, { createContext, useContext } from "react";

export type Role = "user" | "manager" | "finance" | "admin";

interface UserContextType {
  role: Role;
}

export const UserContext = createContext<UserContextType>({ role: "user" });

export const useUser = () => useContext(UserContext); 