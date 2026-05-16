/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: '#0B1020',
          subtle: '#111827',
          card: '#161E2E',
        },
        border: {
          DEFAULT: '#263247',
        },
        fg: {
          DEFAULT: '#E5E7EB',
          muted: '#9CA3AF',
          dim: '#6B7280',
        },
        st: {
          planned: '#6B7280',
          ready: '#38BDF8',
          in_progress: '#60A5FA',
          blocked: '#F97316',
          review: '#A78BFA',
          done: '#22C55E',
          skipped: '#64748B',
          cancelled: '#EF4444',
        },
        pri: {
          low: '#64748B',
          medium: '#38BDF8',
          high: '#F59E0B',
          critical: '#EF4444',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
}
