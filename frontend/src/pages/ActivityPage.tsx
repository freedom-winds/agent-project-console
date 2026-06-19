import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api } from '../api'

const ACTION_COLORS: Record<string, string> = {
  project_created: 'text-st-done',
  project_updated: 'text-st-in_progress',
  node_created: 'text-st-ready',
  node_updated: 'text-st-in_progress',
  node_deleted: 'text-st-cancelled',
  node_moved: 'text-st-review',
  status_changed: 'text-st-in_progress',
  evidence_added: 'text-st-done',
  artifact_added: 'text-st-done',
  checkpoint_created: 'text-st-review',
  blocker_reported: 'text-st-blocked',
  focus_set: 'text-st-ready',
  token_created: 'text-fg-muted',
  token_revoked: 'text-fg-muted',
}

export default function ActivityPage() {
  const { id } = useParams()
  const { t } = useTranslation()
  const [items, setItems] = useState<any[]>([])

  const load = () => api.listActivity(id!, 500).then(d => setItems(d.activities || []))
  useEffect(() => {
    load()
    const timer = setInterval(load, 3000)
    return () => clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  return (
    <div className="p-6">
      <h2 className="mb-4 text-xl font-semibold">{t('activity_log')}</h2>
      <div className="card divide-y divide-border">
        {items.length === 0 ? (
          <div className="p-8 text-center text-fg-dim">{t('no_activity')}</div>
        ) : (
          items.map(a => (
            <div key={a.id} className="p-3">
              <div className="flex items-center gap-2 text-sm">
                <span className={`font-mono text-xs ${ACTION_COLORS[a.action_type] || 'text-fg-muted'}`}>{a.action_type}</span>
                <span className="text-fg-dim">·</span>
                <span className="text-fg-muted">{t('by_actor', { actor: a.actor })}</span>
                <span className="ml-auto text-xs text-fg-dim">{new Date(a.created_at).toLocaleString()}</span>
              </div>
              {a.reason && <div className="mt-1 text-xs text-fg-muted">{t('reason_label', { reason: a.reason })}</div>}
              {(a.before || a.after) && (
                <details className="mt-1">
                  <summary className="cursor-pointer text-xs text-fg-dim">{t('diff_label')}</summary>
                  <div className="mt-2 grid gap-2 text-xs md:grid-cols-2">
                    <pre className="rounded bg-bg-subtle p-2 font-mono text-fg-muted overflow-auto max-h-48">{JSON.stringify(a.before, null, 2)}</pre>
                    <pre className="rounded bg-bg-subtle p-2 font-mono text-fg-muted overflow-auto max-h-48">{JSON.stringify(a.after, null, 2)}</pre>
                  </div>
                </details>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
