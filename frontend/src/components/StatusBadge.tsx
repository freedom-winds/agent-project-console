import { STATUS_CN, STATUS_COLOR, StatusKind } from '../api'

export function StatusBadge({ status }: { status: string }) {
  const k = (status as StatusKind) || 'planned'
  const cls = STATUS_COLOR[k] || STATUS_COLOR.planned
  const cn = STATUS_CN[k] || status
  return (
    <span className={`badge ${cls}`}>
      {status}
      <span className="text-fg-dim">·</span>
      <span>{cn}</span>
    </span>
  )
}

export function PriorityBadge({ priority }: { priority: string }) {
  const map: Record<string, string> = {
    low: 'bg-pri-low/20 text-pri-low border border-pri-low/40',
    medium: 'bg-pri-medium/20 text-pri-medium border border-pri-medium/40',
    high: 'bg-pri-high/20 text-pri-high border border-pri-high/40',
    critical: 'bg-pri-critical/20 text-pri-critical border border-pri-critical/40',
  }
  return <span className={`badge ${map[priority] || map.medium}`}>{priority}</span>
}

export function ProgressBar({ value, color = '#60A5FA' }: { value: number; color?: string }) {
  return (
    <div className="h-1.5 w-full rounded-full bg-[#0F1626]">
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${Math.max(0, Math.min(100, value))}%`, backgroundColor: color }}
      />
    </div>
  )
}
