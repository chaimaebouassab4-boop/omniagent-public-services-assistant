import type { Config } from "tailwindcss";
import forms from "@tailwindcss/forms";
import typography from "@tailwindcss/typography";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "#EAC79F",
        input: "#EAC79F",
        ring: "#3F7A38",
        background: "#F8EFD8",
        foreground: "#111A33",
        primary: {
          DEFAULT: "#D96A50",
          foreground: "hsl(0 0% 100%)"
        },
        secondary: {
          DEFAULT: "#3F7A38",
          foreground: "#FFFFFF"
        },
        civic: {
          teal: "#3F7A38",
          indigo: "#111A33",
          amber: "#D96A50",
          rose: "#D96A50"
        }
      },
      boxShadow: {
        panel: "0 8px 30px rgba(15, 23, 42, 0.06)"
      },
      keyframes: {
        slideInBottom: {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" }
        },
        slideInLeft: {
          "0%": { transform: "translateX(-20px)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" }
        },
        slideInRight: {
          "0%": { transform: "translateX(20px)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" }
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(15, 118, 110, 0.4)" },
          "50%": { boxShadow: "0 0 0 10px rgba(15, 118, 110, 0)" }
        }
      },
      animation: {
        "slide-in-bottom": "slideInBottom 0.45s ease-out",
        "slide-in-left": "slideInLeft 0.45s ease-out",
        "slide-in-right": "slideInRight 0.45s ease-out",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite"
      }
    }
  },
  plugins: [forms, typography]
};

export default config;
