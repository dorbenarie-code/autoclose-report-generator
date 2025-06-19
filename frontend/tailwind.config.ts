import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    fontFamily: {
      sans: ['Inter', 'sans-serif'],
    },
    extend: {
      colors: {
        primary: "#2563eb",
        critical: "#dc2626",
        success: "#16a34a",
        gray: {
          base: "#1e293b",
          bg: "#f8fafc",
        },
      },
      screens: {
        '2xl': '1440px',
        'xl': '1024px',
        'lg': '1024px',
        'md': '768px',
        'sm': '480px',
      },
    },
  },
  darkMode: 'class',
  plugins: [],
}

export default config

