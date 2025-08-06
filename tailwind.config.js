/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./frontend-src/index.html",
    "./frontend-src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gray: {
          900: '#0f0f0f',
          800: '#1a1a1a',
          700: '#2a2a2a',
        },
      },
    },
  },
  plugins: [],
}
