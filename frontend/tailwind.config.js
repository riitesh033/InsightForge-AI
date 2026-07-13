/** @type {import('tailwindcss').Config} */

module.exports = {

  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],

  theme: {

    extend: {

      colors: {

        primary: "#4F46E5",
        secondary: "#F1F5F9",

        success: "#10B981",

        warning: "#F59E0B",

        danger: "#EF4444",

      },

      borderRadius: {

        xl: "16px",

        "2xl": "20px",

      },

      boxShadow: {

        card:
          "0 10px 25px rgba(0,0,0,.08)",

        glow:
          "0 0 40px rgba(79,70,229,.25)",

      },

      maxWidth: {

        content: "1280px",

      },

      transitionTimingFunction: {

        smooth: "cubic-bezier(.4,0,.2,1)",

      },

    },

  },

  plugins: [],

};