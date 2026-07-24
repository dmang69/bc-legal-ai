/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0b1020',
        panel: '#10172b',
        card: '#18213b',
        border: '#2a3558',
        text: '#e9eefc',
        muted: '#98a2c7',
        accent: '#4a67cf',
      },
    },
  },
  plugins: [],
};
