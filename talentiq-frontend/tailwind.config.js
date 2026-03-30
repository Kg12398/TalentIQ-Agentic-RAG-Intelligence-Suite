/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        hr: {
          primary: "#4F46E5", // Indigo 600
          secondary: "#6366F1", // Indigo 500
          dark: "#1E293B", // Slate 800
          light: "#F8FAFC", // Slate 50
          accent: "#10B981", // Emerald 500
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
