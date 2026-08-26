import forms from "@tailwindcss/forms";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#090B12",
        surface: "#121826",
        surfaceAlt: "#1B2233",
        stroke: "#243047",
        brand: "#3B82F6",
        accent: "#10B981",
        warning: "#F59E0B",
        danger: "#EF4444",
      },
      boxShadow: {
        soft: "0 20px 45px rgba(3, 7, 18, 0.28)",
      },
      borderRadius: {
        "2xl": "1.25rem",
      },
    },
  },
  plugins: [forms],
};
