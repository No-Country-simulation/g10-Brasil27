/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border, 217 19% 27%))",
        background: "hsl(var(--background, 222 47% 11%))",
        foreground: "hsl(var(--foreground, 210 40% 98%))",
      }
    },
  },
  plugins: [],
}
