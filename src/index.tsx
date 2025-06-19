import React from "react";
import ReactDOM from "react-dom/client";
import "./styles/tailwind.css";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider } from "./app/ThemeProvider";
import Router from "./app/router";
import { UserContext, Role } from "./app/UserContext";

const role: Role = "admin";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <UserContext.Provider value={{ role }}>
      <ThemeProvider>
        <BrowserRouter>
          <Router />
        </BrowserRouter>
      </ThemeProvider>
    </UserContext.Provider>
  </React.StrictMode>
); 