import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0B0F1A",
        card: "#0F1526",
        accent: "#7C5CFF",
        accent2: "#12D8FA",
        text: "#E6EAF2",
        subt: "#9AA3B2"
      },
      boxShadow: {
        glow: "0 0 80px rgba(124, 92, 255, 0.25)"
      },
      borderRadius: {
        xl2: "1.25rem"
      }
    }
  },
  plugins: [require("@tailwindcss/typography")]
};

export default config;
