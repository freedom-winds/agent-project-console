import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { StatusBadge, PriorityBadge, ProgressBar } from './StatusBadge'

interface Props {
  nodeId: string
  onClose: () => void
  onChanged?: () => void
}

const TABS = ['Overview', 'Evidence', 'Artifacts', 'Notes', 'History'] as const
type Tab = (typeof TABS)[number]

export function StepDrawer({ nodeId, onClose, onChanged }: Props) {
  const [tab, setTab] = useState<Tab>('Overview')
  const [node, setNode] = useState<any>(null)
  const [history, setHistory] = useState<any[]>([])
  const [error, setError] = useState<string>('')
  const { t } = useTranslation()
  const [statusForm, setStatusForm] = useState({
    status: '',
    evidence_summary: '',
    blocker_reason: '',
    next_action: '',
    impact: '',
    reason: '',
  })
  const [evidenceForm, setEvidenceForm] = useState({
    evidence_type: 'note',
    title: '',
    content: '',
    summary: '',
  })
  const [artifactForm, setArtifactForm] = useState({
    artifact_type: 'document',
    title: '',
    path_or_url: '',
    summary: '',
  })

  const reload = () => {
    setError('')
    api
      .getNode(nodeId)
      .then(n => {
        setNode(n)
        setStatusForm(s => ({ ...s, status: n.status }))
      })
      .catch(e => setError(e.message))
    if (node?.project_id) {
      api.listActivity(node.project_id, 100).then(d => {
        setHistory((d.activities || []).filter((a: any) => a.node_id === nodeId))
      })
    }
  }

  useEffect(() => {
    reload()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodeId])

  useEffect(() => {
    if (node?.project_id) {
      api.listActivity(node.project_id, 100).then(d => {
        setHistory((d.activities || []).filter((a: any) => a.node_id === nodeId))
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [node?.project_id, nodeId])

  const submitStatus = async () => {
    setError('')
    try {
      await api.updateStatus(nodeId, statusForm)
      reload()
      onChanged?.()
    } catch (e: any) {
      setError(e.message)
    }
  }

  const submitEvidence = async () => {
    setError('')
    try {
      await api.addEvidence(nodeId, evidenceForm)
      setEvidenceForm({ evidence_type: 'note', title: '', content: '', summary: '' })
      reload()
      onChanged?.()
    } catch (e: any) {
      setError(e.message)
    }
  }

  const submitArtifact = async () => {
    setError('')
    try {
      await api.addArtifact(nodeId, artifactForm)
      setArtifactForm({ artifact_type: 'document', title: '', path_or_url: '', summary: '' })
      reload()
      onChanged?.()
    } catch (e: any) {
      setError(e.message)
    }
  }

  if (!node) {
    return (
      <div className="fixed right-0 top-0 z-30 h-full w-[420px] border-l border-border bg-bg-card p-4">
        {t('loading')}
      </div>
    )
  }

  return (
    <div className="fixed right-0 top-0 z-30 flex h-full w-[420px] flex-col border-l border-border bg-bg-card">
      <div className="flex items-center justify-between border-b border-border p-4">
        <div>
          <div className="text-xs uppercase tracking-wide text-fg-dim">{node.node_type}</div>
          <h3 className="text-base font-semibold">{node.title}</h3>
        </div>
        <button onClick={onClose} className="rounded p-1 hover:bg-bg-subtle">
          <X size={18} />
        </button>
      </div>

      <div className="flex border-b border-border">
        {TABS.map(tabName => (
          <button
            key={tabName}
            className={`px-3 py-2 text-sm ${tab === tabName ? 'border-b-2 border-st-in_progress text-fg' : 'text-fg-muted'}`}
            onClick={() => setTab(tabName)}
          >
            {tabName}
          </button>
        ))}
      </div>

      {error && <div className="m-3 rounded border border-st-cancelled/40 bg-st-cancelled/10 p-2 text-xs text-st-cancelled">{error}</div>}

      <div className="flex-1 overflow-auto p-4">
        {tab === 'Overview' && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <StatusBadge status={node.status} />
              <PriorityBadge priority={node.priority} />
            </div>
            <ProgressBar value={node.progress || 0} />
            <div>
              <div className="text-xs text-fg-dim">{t('drawer_description')}</div>
              <div className="whitespace-pre-wrap text-sm">{node.description || '—'}</div>
            </div>
            <div>
              <div className="text-xs text-fg-dim">{t('drawer_acceptance')}</div>
              <div className="whitespace-pre-wrap text-sm">{node.acceptance_criteria || '—'}</div>
            </div>
            <div>
              <div className="text-xs text-fg-dim">{t('drawer_evidence_summary')}</div>
              <div className="whitespace-pre-wrap text-sm">{node.evidence_summary || '—'}</div>
            </div>
            {node.status === 'blocked' && (
              <div className="rounded border border-st-blocked/40 bg-st-blocked/10 p-3 text-sm">
                <div className="mb-1 font-medium text-st-blocked">{t('drawer_blocker')}</div>
                <div className="text-xs text-fg-muted">{t('drawer_blocker_reason')}</div>
                <div>{node.blocker_reason || '—'}</div>
                <div className="mt-1 text-xs text-fg-muted">{t('drawer_blocker_impact')}</div>
                <div>{node.blocker_impact || '—'}</div>
                <div className="mt-1 text-xs text-fg-muted">{t('drawer_blocker_next')}</div>
                <div>{node.next_action || '—'}</div>
              </div>
            )}

            <div className="card mt-3 p-3">
              <div className="mb-2 text-sm font-medium">{t('drawer_update_status')}</div>
              <select
                className="input mb-2 w-full"
                value={statusForm.status}
                onChange={e => setStatusForm({ ...statusForm, status: e.target.value })}
              >
                {['planned', 'ready', 'in_progress', 'blocked', 'review', 'done', 'skipped', 'cancelled'].map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              {statusForm.status === 'done' && (
                <textarea
                  className="input mb-2 w-full"
                  placeholder={t('placeholder_evidence_summary')}
                  rows={2}
                  value={statusForm.evidence_summary}
                  onChange={e => setStatusForm({ ...statusForm, evidence_summary: e.target.value })}
                />
              )}
              {statusForm.status === 'blocked' && (
                <>
                  <input
                    className="input mb-2 w-full"
                    placeholder={t('placeholder_blocker_reason')}
                    value={statusForm.blocker_reason}
                    onChange={e => setStatusForm({ ...statusForm, blocker_reason: e.target.value })}
                  />
                  <input
                    className="input mb-2 w-full"
                    placeholder={t('placeholder_blocker_impact')}
                    value={statusForm.impact}
                    onChange={e => setStatusForm({ ...statusForm, impact: e.target.value })}
                  />
                  <input
                    className="input mb-2 w-full"
                    placeholder={t('placeholder_blocker_next')}
                    value={statusForm.next_action}
                    onChange={e => setStatusForm({ ...statusForm, next_action: e.target.value })}
                  />
                </>
              )}
              <input
                className="input mb-2 w-full"
                placeholder={t('placeholder_override_reason')}
                value={statusForm.reason}
                onChange={e => setStatusForm({ ...statusForm, reason: e.target.value })}
              />
              <button className="btn-primary w-full" onClick={submitStatus}>{t('drawer_apply')}</button>
            </div>
          </div>
        )}

        {tab === 'Evidence' && (
          <div className="space-y-3">
            <EvidenceList nodeId={nodeId} />
            <div className="card p-3">
              <div className="mb-2 text-sm font-medium">{t('drawer_add_evidence')}</div>
              <select
                className="input mb-2 w-full"
                value={evidenceForm.evidence_type}
                onChange={e => setEvidenceForm({ ...evidenceForm, evidence_type: e.target.value })}
              >
                {['note', 'file_path', 'commit_hash', 'command_output', 'test_result', 'screenshot_path', 'url'].map(et => (
                  <option key={et} value={et}>{et}</option>
                ))}
              </select>
              <input className="input mb-2 w-full" placeholder="title" value={evidenceForm.title} onChange={e => setEvidenceForm({ ...evidenceForm, title: e.target.value })} />
              <textarea className="input mb-2 w-full" rows={2} placeholder={t('placeholder_content')} value={evidenceForm.content} onChange={e => setEvidenceForm({ ...evidenceForm, content: e.target.value })} />
              <textarea className="input mb-2 w-full" rows={2} placeholder={t('placeholder_summary')} value={evidenceForm.summary} onChange={e => setEvidenceForm({ ...evidenceForm, summary: e.target.value })} />
              <button className="btn-primary w-full" onClick={submitEvidence}>{t('btn_add')}</button>
            </div>
          </div>
        )}

        {tab === 'Artifacts' && (
          <div className="space-y-3">
            <ArtifactList nodeId={nodeId} />
            <div className="card p-3">
              <div className="mb-2 text-sm font-medium">{t('drawer_add_artifact')}</div>
              <input className="input mb-2 w-full" placeholder={t('placeholder_artifact_type')} value={artifactForm.artifact_type} onChange={e => setArtifactForm({ ...artifactForm, artifact_type: e.target.value })} />
              <input className="input mb-2 w-full" placeholder="title" value={artifactForm.title} onChange={e => setArtifactForm({ ...artifactForm, title: e.target.value })} />
              <input className="input mb-2 w-full" placeholder={t('placeholder_path_or_url')} value={artifactForm.path_or_url} onChange={e => setArtifactForm({ ...artifactForm, path_or_url: e.target.value })} />
              <textarea className="input mb-2 w-full" rows={2} placeholder={t('placeholder_summary')} value={artifactForm.summary} onChange={e => setArtifactForm({ ...artifactForm, summary: e.target.value })} />
              <button className="btn-primary w-full" onClick={submitArtifact}>{t('btn_add')}</button>
            </div>
          </div>
        )}

        {tab === 'Notes' && (
          <div className="space-y-2">
            <div className="text-xs text-fg-dim">{t('drawer_latest_note')}</div>
            <div className="whitespace-pre-wrap text-sm">{node.latest_note || '—'}</div>
          </div>
        )}

        {tab === 'History' && (
          <div className="space-y-2">
            {history.length === 0 ? (
              <div className="text-sm text-fg-dim">{t('drawer_no_history')}</div>
            ) : (
              history.map(h => (
                <div key={h.id} className="rounded border border-border p-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{h.action_type}</span>
                    <span className="text-fg-dim">{new Date(h.created_at).toLocaleString()}</span>
                  </div>
                  <div className="text-fg-muted">{t('by_actor', { actor: h.actor })}</div>
                  {h.reason && <div className="mt-1 text-fg-muted">{t('reason_label', { reason: h.reason })}</div>}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function EvidenceList({ nodeId }: { nodeId: string }) {
  const [items, setItems] = useState<any[]>([])
  useEffect(() => {
    api.listEvidence(nodeId).then(d => setItems(d.evidences || []))
  }, [nodeId])
  if (items.length === 0) return <div className="text-sm text-fg-dim">No evidence yet.</div>
  return (
    <div className="space-y-2">
      {items.map(e => (
        <div key={e.id} className="rounded border border-border p-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="font-medium">{e.title}</span>
            <span className="badge bg-bg-subtle text-fg-muted">{e.evidence_type}</span>
          </div>
          {e.content && <code className="block break-all font-mono text-xs text-fg-muted">{e.content}</code>}
          {e.summary && <div className="mt-1 text-xs text-fg-muted">{e.summary}</div>}
        </div>
      ))}
    </div>
  )
}

function ArtifactList({ nodeId }: { nodeId: string }) {
  const [items, setItems] = useState<any[]>([])
  useEffect(() => {
    api.listArtifacts(nodeId).then(d => setItems(d.artifacts || []))
  }, [nodeId])
  if (items.length === 0) return <div className="text-sm text-fg-dim">No artifacts yet.</div>
  return (
    <div className="space-y-2">
      {items.map(a => (
        <div key={a.id} className="rounded border border-border p-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="font-medium">{a.title}</span>
            <span className="badge bg-bg-subtle text-fg-muted">{a.artifact_type}</span>
          </div>
          {a.path_or_url && <div className="font-mono text-xs text-fg-muted">{a.path_or_url}</div>}
          {a.summary && <div className="text-xs text-fg-muted">{a.summary}</div>}
        </div>
      ))}
    </div>
  )
}
