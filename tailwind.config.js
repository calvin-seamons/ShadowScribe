/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./frontend-src/index.html",
    "./frontend-src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gray: {
          900: '#0f0f0f',
          800: '#1a1a1a',
          750: '#1f1f1f',
          700: '#2a2a2a',
        },
      },
      typography: {
        DEFAULT: {
          css: {
            color: '#f3f4f6',
            '[class~="lead"]': {
              color: '#e5e7eb',
            },
            a: {
              color: '#60a5fa',
              '&:hover': {
                color: '#93c5fd',
              },
            },
            strong: {
              color: '#f3f4f6',
            },
            'ol > li::before': {
              color: '#9ca3af',
            },
            'ul > li::before': {
              backgroundColor: '#9ca3af',
            },
            hr: {
              borderColor: '#374151',
            },
            blockquote: {
              color: '#e5e7eb',
              borderLeftColor: '#9333ea',
            },
            h1: {
              color: '#f3f4f6',
            },
            h2: {
              color: '#f3f4f6',
            },
            h3: {
              color: '#f3f4f6',
            },
            h4: {
              color: '#f3f4f6',
            },
            'figure figcaption': {
              color: '#9ca3af',
            },
            code: {
              color: '#f3f4f6',
            },
            'a code': {
              color: '#f3f4f6',
            },
            pre: {
              color: '#e5e7eb',
              backgroundColor: '#1f2937',
            },
            thead: {
              color: '#f3f4f6',
              borderBottomColor: '#374151',
            },
            'tbody tr': {
              borderBottomColor: '#374151',
            },
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
