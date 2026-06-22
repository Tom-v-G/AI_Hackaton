/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#080f1f",
        "surface-raised": "#101a31",
        "surface-border": "#23304f",
        accent: "#38bdf8",
      },
    },
  },
  plugins: [],
};
