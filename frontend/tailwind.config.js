/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ivory': '#F5F5F0',
        'vermillion': '#E53935',
        'zinc-950': '#09090b',
        'zinc-900': '#18181b',
        'zinc-800': '#27272a',
      },
      fontFamily: {
        serif: ['"Libre Baskerville"', 'serif'],
        mono: ['"Space Mono"', 'monospace'],
        sans: ['"Space Grotesk"', 'sans-serif'], 
      },
      typography: (theme) => ({
        DEFAULT: {
          css: {
            color: theme('colors.ivory'),
            h1: {
              fontFamily: theme('fontFamily.serif')[0],
              color: theme('colors.ivory'),
              fontWeight: '700',
              fontSize: '2.5rem',
              marginTop: '0',
            },
            h2: {
              fontFamily: theme('fontFamily.serif')[0],
              color: theme('colors.ivory'),
              borderBottom: '1px solid ' + theme('colors.zinc-800'),
              paddingBottom: '0.5rem',
              fontWeight: '400',
            },
            h3: {
              fontFamily: theme('fontFamily.serif')[0],
              color: theme('colors.vermillion'),
            },
            a: {
              color: theme('colors.vermillion'),
            },
            strong: {
              color: theme('colors.ivory'),
              fontWeight: '700',
            },
            ul: {
              listStyleType: 'square',
            },
            code: {
              color: theme('colors.vermillion'),
              fontFamily: theme('fontFamily.mono')[0],
            }
          },
        },
      }),
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
