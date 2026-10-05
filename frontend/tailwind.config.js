/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: "#0b0f19",
          card: "#131b2e",
          accent: "#00f2fe",
          purple: "#7928ca",
          pink: "#ff0080",
          success: "#10b981",
          warning: "#f59e0b",
          danger: "#ef4444"
        }
      }
    },
  },
  plugins: [],
}
