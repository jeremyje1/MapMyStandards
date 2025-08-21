/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./*.html",
    "./**/*.html",
    "./static/**/*.js",
    "!./node_modules/**/*"
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#3b82f6',
        'secondary': '#10b981',
        'accent': '#f59e0b',
      }
    },
  },
  plugins: [],
}
