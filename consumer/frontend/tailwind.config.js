/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        leaf: "#1f7a4d",
        mist: "#f3f7f2",
        ink: "#1c2b22",
      },
    },
  },
  plugins: [],
};
