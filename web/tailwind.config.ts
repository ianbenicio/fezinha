import type { Config } from "tailwindcss";

export default {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fz: {
          green: "#16a34a",
          dark: "#0a0f0d",
          card: "#11201a",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
