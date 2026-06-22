/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#080f1f",
        "surface-raised": "#101a31",
        "surface-border": "#23304f",
        accent: "#39ff88",
        // Re-tint the emerald ramp toward the bright "matrix" green so the
        // existing emerald-* classes read as neon tech-green, not soft mint.
        emerald: {
          50: "#eaffef",
          100: "#d6ffe5",
          200: "#9dffc2",
          300: "#39ff88",
          400: "#43c476",
          500: "#2fae6a",
          600: "#1f8a51",
          700: "#16633a",
          800: "#0d3d24",
          900: "#072115",
          950: "#04120a",
        },
      },
      fontFamily: {
        sans: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      // Sharper, more "tech" corners across the board (threatpulse uses 3-6px).
      borderRadius: {
        none: "0",
        sm: "2px",
        DEFAULT: "3px",
        md: "3px",
        lg: "4px",
        xl: "5px",
        "2xl": "6px",
        "3xl": "6px",
        full: "9999px",
      },
    },
  },
  plugins: [],
};
