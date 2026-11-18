/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        base: "#F6F8FB",
        surface: "#FFFFFF",
        subtle: "#EDF1F7",
        border: "#DCE3EE",
        textPrimary: "#0F1E33",
        textSecondary: "#4A5C75",
        textMuted: "#7C8CA3",
        primary: {
          DEFAULT: "#1D4ED8",
          hover: "#1E40AF",
          soft: "#DBEAFE",
        },
        transit: {
          blue: "#1D4ED8",
          emerald: "#059669",
          amber: "#D97706",
          rose: "#E11D48",
          violet: "#7C3AED",
          sky: "#0284C7",
          lime: "#65A30D",
          orange: "#EA580C",
        },
        ontime: {
          text: "#15803D",
          chart: "#22C55E",
          soft: "#DCFCE7",
        },
        minor: {
          text: "#B45309",
          chart: "#F59E0B",
          soft: "#FEF3C7",
        },
        major: {
          text: "#B91C1C",
          chart: "#EF4444",
          soft: "#FEE2E2",
        },
        prediction: {
          text: "#6D28D9",
          chart: "#8B5CF6",
          soft: "#EDE9FE",
        },
        teal: {
          DEFAULT: "#0D9488",
          soft: "#CCFBF1",
        },
      },
      borderRadius: {
        card: "12px",
        input: "8px",
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(15, 30, 51, 0.06), 0 1px 2px -1px rgba(15, 30, 51, 0.04)",
        cardHover: "0 4px 6px -1px rgba(15, 30, 51, 0.08), 0 2px 4px -2px rgba(15, 30, 51, 0.04)",
        dropdown: "0 10px 15px -3px rgba(15, 30, 51, 0.1), 0 4px 6px -4px rgba(15, 30, 51, 0.05)",
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [
    require("tailwindcss-animate"),
  ],
};
