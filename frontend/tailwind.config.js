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
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae0fd',
          300: '#7cc8fb',
          400: '#36abf7',
          500: '#0c8ee9',
          600: '#0270c7',
          700: '#0359a1',
          800: '#074c84',
          900: '#0c406e',
          950: '#082949',
        },
        verified: {
          light: '#ecfdf5',
          border: '#10b981',
          text: '#065f46',
          badge: '#059669',
        },
        blocked: {
          light: '#fef2f2',
          border: '#ef4444',
          text: '#991b1b',
          badge: '#dc2626',
        },
        review: {
          light: '#fffbeb',
          border: '#f59e0b',
          text: '#92400e',
          badge: '#d97706',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}
