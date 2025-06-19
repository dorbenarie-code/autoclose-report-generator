import React from "react"
import { createContext, useContext, useEffect, useState } from "react"

export type Theme = "light" | "dark"

const ThemeContext = createContext<{ theme: Theme; toggle: () => void }>(
  { theme: "light", toggle: () => {} }
)

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>(() =>
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
  )

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark")
  }, [theme])

  const toggle = () => setTheme(t => (t === "light" ? "dark" : "light"))

  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
