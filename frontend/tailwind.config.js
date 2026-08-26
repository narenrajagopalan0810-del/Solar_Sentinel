/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sonar: {
          950: '#060b13',
          900: '#0b1322',
          850: '#0f1b2e',
          800: '#15243c',
          700: '#1e3352',
          600: '#2c4b75',
          cyan: '#00e5ff',
          emerald: '#00f59b',
          amber: '#ffb300',
          hazard: '#ff3366',
        }
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
