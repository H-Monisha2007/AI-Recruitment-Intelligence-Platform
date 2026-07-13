/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#000000",
        secondary: "#FFFFFF",
        accent: "#71717a", // zinc-500
        background: "#FFFFFF",
        card: "#f4f4f5", // zinc-100
      },
      backgroundColor: {
        'pure-black': '#000000',
        'pure-white': '#FFFFFF',
      },
      textColor: {
        'pure-black': '#000000',
        'pure-white': '#FFFFFF',
      }
    },
  },
  plugins: [],
}
