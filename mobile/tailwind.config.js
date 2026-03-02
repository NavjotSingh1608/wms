/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        primary: "#1e40af",
        secondary: "#1e3a5f",
        quarantine: "#f59e0b",
        approved: "#10b981",
        rejected: "#ef4444",
        undertest: "#6366f1",
      },
    },
  },
  plugins: [],
};
