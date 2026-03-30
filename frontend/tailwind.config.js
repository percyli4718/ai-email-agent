/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 主色调 - 蓝色系
        primary: '#60a5fa',
        primaryDark: '#3b82f6',
        // 次要色 - 紫色系
        secondary: '#a855f7',
        // 强调色 - 橙色系 (Agent 主题)
        accent: '#f97316',
        accentLight: '#fb923c',
        // 状态色
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        // 背景色 - 深色主题
        bg: {
          main: '#0a0e1a',
          card: '#1e293b',
          panel: '#0f172a',
        },
        // 文本色
        text: {
          primary: '#e2e8f0',
          secondary: '#94a3b8',
          muted: '#64748b',
        },
        // 边框色
        border: {
          light: '#334155',
          DEFAULT: '#475569',
          dark: '#1e293b',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['SF Mono', 'Monaco', 'Inconsolata', 'monospace'],
      },
      backgroundImage: {
        'agent-gradient': 'linear-gradient(145deg, rgba(249,115,22,0.1), rgba(15,23,42,0.5))',
        'card-gradient': 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
        'header-gradient': 'linear-gradient(90deg, #1e293b, #334155)',
        'budget-gradient': 'linear-gradient(90deg, #f97316, #fb923c)',
      },
      boxShadow: {
        'glow-green': '0 0 10px #10b981',
        'glow-yellow': '0 0 10px #f59e0b',
        'card': '0 10px 40px rgba(0,0,0,0.4)',
      },
      animation: {
        'slide-in': 'slideIn 0.3s ease-out forwards',
        'fade-in': 'fadeIn 0.2s ease-in forwards',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateX(-10px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
