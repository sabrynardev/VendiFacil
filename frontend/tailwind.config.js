import forms from "@tailwindcss/forms";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#F4F8FF",
        surface: "#FFFFFF",
        surfaceAlt: "#EAF1FF",
        stroke: "#D7E3FF",
        brand: "#023BE6",
        brandDark: "#011C6B",
        brandDeeper: "#011142",
        brandMid: "#01258F",
        brandStrong: "#0231BD",
        accent: "#01258F",
        warning: "#D97706",
        danger: "#D92D20",
      },
      boxShadow: {
        soft: "0 24px 60px rgba(1, 28, 107, 0.12)",
      },
      borderRadius: {
        "2xl": "1.25rem",
      },
    },
  },
  plugins: [forms],
};
