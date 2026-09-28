import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#F7F7F5",
        surface: "#FFFFFF",
        subtle: "#FAFAF9",
        border: {
          DEFAULT: "#E7E7E3",
          hover: "#D4D4D0",
        },
        primary: {
          text: "#171717",
        },
        secondary: {
          text: "#737373",
        },
        muted: {
          text: "#A3A3A3",
        },
        accent: {
          DEFAULT: "#3157D5",
          hover: "#2646B8",
          subtle: "#EEF2FF",
        },
        success: {
          DEFAULT: "#16803C",
          subtle: "#ECFDF3",
          border: "#A6F4C5",
        },
        warning: {
          DEFAULT: "#B7791F",
          subtle: "#FEFCE8",
          border: "#FEF08A",
        },
        danger: {
          DEFAULT: "#C53030",
          subtle: "#FEF2F2",
          border: "#FECACA",
        },
      },
      borderRadius: {
        control: "7px",
        card: "11px",
        dialog: "14px",
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
