import { useEffect, useState } from 'react'
import { useParams, useOutletContext } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Plus } from 'lucide-react'
import { api } from '../api'

export default function CheckpointsPage() {
  const { id } = useParams()
  const { reload } = useOutletContext<any>()
  const { t } = useTranslation()
  const [items, setItems] = useState<any[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({
    agent_name: '',
    summary: '',
    completed: '',
    in_progress: '',
    next: '',
    blockers: '',
    risks: '',
  })
  const [error, setError] = useState('')

  const load = () => api.listCheckpoints(id!).then(d => setItems(d.checkpoints || []))
  useEffect(() => {
    load()
    const timer = setInterval(load, 3000)
    return () => clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const splitLines = (s: string) => s.split(/\n+/).map(x => x.trim()).filter(Boolean)

  const submit = async () => {
    setError('')
    try {
      await api.createCheckpoint(id!, {
        agent_name: form.agent_name || 'human',
        summary: form.summary,
        completed: splitLines(form.completed),
        in_progress: splitLines(form.in_progress),
        next: splitLines(form.next),
        blockers: splitLines(form.blockers),
        risks: splitLines(form.risks),
      })
      setShowCreate(false)
      setForm({ agent_name: '', summary: '', completed: '', in_progress: '', next: '', blockers: '', risks: '' })
      load()
      reload?.()
    } catch (e: any) {
      setError(e.message)
    }
  }

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">{t('tab_checkpoints')}</h2>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={14} /> {t('new_checkpoint')}
        </button>
      </div>

      {showCreate && (
        <div className="card mb-4 p-4">
          {error && <div className="mb-3 rounded border border-st-cancelled/40 bg-st-cancelled/10 p-2 text-xs text-st-cancelled">{error}</div>}
          <div className="grid gap-2 md:grid-cols-2">
            <input className="input" placeholder={t('placeholder_agent_name')} value={form.agent_name} onChange={e => setForm({ ...form, agent_name: e.target.value })} />
            <input className="input" placeholder={t('placeholder_summary')} value={form.summary} onChange={e => setForm({ ...form, summary: e.target.value })} />
            <textarea className="input" rows={3} placeholder={t('placeholder_completed')} value={form.completed} onChange={e => setForm({ ...form, completed: e.target.value })} />
            <textarea className="input" rows={3} placeholder={t('placeholder_in_progress')} value={form.in_progress} onChange={e => setForm({ ...form, in_progress: e.target.value })} />
            <textarea className="input" rows={3} placeholder={t('placeholder_next')} value={form.next} onChange={e => setForm({ ...form, next: e.target.value })} />
            <textarea className="input" rows={3} placeholder={t('placeholder_blockers')} value={form.blockers} onChange={e => setForm({ ...form, blockers: e.target.value })} />
            <textarea className="input md:col-span-2" rows={2} placeholder={t('placeholder_risks')} value={form.risks} onChange={e => setForm({ ...form, risks: e.target.value })} />
          </div>
          <div className="mt-3 flex gap-2">
            <button className="btn-primary" onClick={submit}>{t('btn_submit')}</button>
            <button className="btn" onClick={() => setShowCreate(false)}>{t('btn_cancel')}</button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {items.length === 0 ? (
          <div className="card p-8 text-center text-fg-dim">{t('no_checkpoints_yet')}</div>
        ) : (
          items.map(cp => (
            <div key={cp.id} className="card p-4">
              <div className="mb-2 flex items-center justify-between">
                <div className="text-sm font-medium">{cp.agent_name || t('unknown_agent')}</div>
                <div className="text-xs text-fg-dim">{new Date(cp.created_at).toLocaleString()}</div>
              </div>
              {cp.summary && <p className="mb-3 text-sm text-fg-muted">{cp.summary}</p>}
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
                <CpList title={t('cp_completed')} items={cp.completed} color="text-st-done" />
                <CpList title={t('cp_in_progress')} items={cp.in_progress} color="text-st-in_progress" />
                <CpList title={t('cp_next')} items={cp.next} color="text-st-ready" />
                <CpList title={t('cp_blockers')} items={cp.blockers} color="text-st-blocked" />
              </div>
              {cp.risks && cp.risks.length > 0 && (
                <div className="mt-3">
                  <div className="text-xs font-medium text-st-review">{t('cp_risks')}</div>
                  <ul className="ml-4 list-disc text-sm text-fg-muted">
                    {cp.risks.map((r: string, i: number) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function CpList({ title, items, color }: { title: string; items: string[]; color: string }) {
  return (
    <div>
      <div className={`mb-1 text-xs font-medium ${color}`}>{title}</div>
      {items && items.length > 0 ? (
        <ul className="ml-4 list-disc space-y-1 text-sm">
          {items.map((s, i) => <li key={i}>{s}</li>)}
        </ul>
      ) : (
        <div className="text-xs text-fg-dim">—</div>
      )}
    </div>
  )
}
