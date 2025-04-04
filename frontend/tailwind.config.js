/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      "./app/**/*.{js,jsx}",
      "./components/**/*.{js,jsx}",
    ],
    theme: {
      extend: {
        colors: {
          primary: "#FDB813", // SolarSync yellow (solar-inspired)
          secondary: "#1E3A8A", // Deep blue (energy-inspired)
          accent: "#10B981", // Green for success states
        },
      },
    },
    plugins: [],
  };