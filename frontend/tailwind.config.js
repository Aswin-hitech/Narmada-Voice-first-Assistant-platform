export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          darkest: '#071527',
          dark: '#0b1c34',
          DEFAULT: '#0f2b54',
          light: '#1c437a',
          surface: '#244f8d',
        },
        saffron: {
          DEFAULT: '#f37021',
          dark: '#d95a0e',
          hover: '#e06014',
          light: '#fff4ec',
          border: '#ffd5be',
        },
        'gov-green': {
          DEFAULT: '#0e8a3a',
          dark: '#0a692b',
          hover: '#0c7a33',
          light: '#e8f8ed',
          border: '#a4e5b9',
        },
        gold: {
          DEFAULT: '#d4af37',
          light: '#fdf8e6',
          border: '#f3e5ab',
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        serif: ['Cinzel', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'glow-saffron': '0 0 16px rgba(243, 112, 33, 0.35)',
        'glow-green': '0 0 16px rgba(14, 138, 58, 0.3)',
      }
    },
  },
  plugins: [],
}
