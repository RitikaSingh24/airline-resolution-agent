import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#FFFBFE",
        surface: "#F3EDF7",
        recessed: "#E7E0EC",
        primary: {
          DEFAULT: "#6750A4",
          hover: "#594296",
        },
        "secondary-container": "#E8DEF8",
        "on-secondary-container": "#1D192B",
        tertiary: "#7D5260",
        "main-text": "#1C1B1F",
        "secondary-text": "#49454F",
        border: "#79747E",
      },
      borderRadius: {
        card: "24px",
      },
    },
  },
  plugins: [],
};

export default config;
