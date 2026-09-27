/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#2F6DF6",
        secondary: "#55B7FF",
        bgLight: "#F8FAFC",
        bgSoft: "#f3f4f6",
        ink: "#111827",
        muted: "#6B7280",
        line: "#E5E7EB",
      },
      fontFamily: {
        display: ["'Fraunces'", "serif"],
        sans: ["'Inter'", "system-ui", "sans-serif"],
      },
      boxShadow: {
        premium: "0 1px 2px rgba(24,24,27,0.04), 0 8px 24px -8px rgba(124,58,237,0.12)",
        soft: "0 1px 2px rgba(24,24,27,0.03)",
      },
      borderRadius: {
        xl2: "1rem",
      },
    },
  },
  plugins: [],
};
