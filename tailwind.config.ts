import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f1729",
        panel: "#17223a",
        panelSoft: "#1d2a45",
        accent: "#ff6b35",
        accentSoft: "#ff8a5f",
        muted: "#95a1b8",
      },
      fontFamily: {
        sans: ["'Nunito Sans'", "sans-serif"],
        display: ["Nunito Sans", "sans-serif"],
      },
      boxShadow: {
        card: "0 12px 30px rgba(4, 10, 25, 0.32)",
      },
    },
  },
  plugins: [],
} satisfies Config;
