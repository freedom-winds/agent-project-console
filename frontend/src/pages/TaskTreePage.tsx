import { useEffect, useMemo, useState } from 'react'
import { useOutletContext, useParams, useSearchParams } from 'react-router-dom'
import { ChevronRight, ChevronDown, Plus, Search, Folder, Layers, FileCheck2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { ProgressBar, StatusBadge, PriorityBadge } from '../components/StatusBadge'
import { StepDrawer } from '../components/StepDrawer'

interface Ctx {
  project: any
  tree: any
  reload: () => void
}

export default function TaskTreePage() {
  const { project, tree, reload } = useOutletContext<Ctx>()
  const { id } = useParams()
  const { t } = useTranslation()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialStep = searchParams.get('step') || ''
  const [selected, setSelected] = useState<string>(initialStep)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState<{ parent?: any; type: 'part' | 'phase' | 'step' } | null>(null)
  const [createForm, setCreateForm] = useState<any>({ title: '', description: '', acceptance_criteria: '', priority: 'medium', reason: '' })
  const [createError, setCreateError] = useState('')

  useEffect(() => {
    if (!tree?.tree) return
    const newSet = new Set<string>()
    for (const p of tree.tree) {
      newSet.add(p.id)
      for (const ph of p.children || []) newSet.add(ph.id)
    }
    setExpanded(s => new Set([...s, ...newSet]))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tree?.project?.id])

  const toggle = (nid: string) => {
    setExpanded(s => {
      const n = new Set(s)
      if (n.has(nid)) n.delete(nid)
      else n.add(nid)
      return n
    })
  }

  const matchesFilter = (n: any) => {
    if (statusFilter && n.status !== statusFilter) return false
    if (search) {
      const q = search.toLowerCase()
      if (!(`${n.title} ${n.description || ''} ${n.evidence_summary || ''}`).toLowerCase().includes(q)) return false
    }
    return true
  }

  const openCreate = (parent: any | undefined, type: 'part' | 'phase' | 'step') => {
    setCreateForm({ title: '', description: '', acceptance_criteria: '', priority: 'medium', reason: '' })
    setCreateError('')
    setCreateOpen({ parent, type })
  }

  const submitCreate = async () => {
    if (!createOpen) return
    setCreateError('')
    try {
      await api.createNode({
        project_id: id,
        parent_id: createOpen.parent?.id || null,
        node_type: createOpen.type,
        title: createForm.title,
        description: createForm.description,
        acceptance_criteria: createForm.acceptance_criteria,
        priority: createForm.priority,
        reason: createForm.reason || 'created via UI',
      })
      setCreateOpen(null)
      reload()
    } catch (e: any) {
      setCreateError(e.message)
    }
  }

  const onChanged = () => reload()

  return (
    <div className="flex h-full">
      <div className="flex-1 overflow-auto p-6">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 rounded border border-border bg-bg-card px-2">
            <Search size={14} className="text-fg-dim" />
            <input
              className="bg-transparent py-1.5 text-sm outline-none"
              placeholder={t('search_placeholder')}
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <select className="input py-1" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
            <option value="">{t('all_statuses')}</option>
            {['planned', 'ready', 'in_progress', 'blocked', 'review', 'done', 'skipped', 'cancelled'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button className="btn-primary ml-auto" onClick={() => openCreate(undefined, 'part')}>
            <Plus size={14} /> {t('add_part')}
          </button>
        </div>

        {(!tree?.tree || tree.tree.length === 0) ? (
          <div className="card p-8 text-center text-fg-dim">{t('no_nodes')}</div>
        ) : (
          <div className="space-y-1">
            {tree.tree.map((part: any) => (
              <NodeRow
                key={part.id}
                node={part}
                depth={0}
                expanded={expanded}
                toggle={toggle}
                selected={selected}
                onSelect={(nid: string) => { setSelected(nid); setSearchParams({ step: nid }) }}
                openCreate={openCreate}
                matchesFilter={matchesFilter}
                t={t}
              />
            ))}
          </div>
        )}
      </div>

      {selected && <StepDrawer nodeId={selected} onClose={() => { setSelected(''); setSearchParams({}) }} onChanged={onChanged} />}

      {createOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-4">
          <div className="card w-full max-w-md p-5">
            <h2 className="mb-3 text-lg font-medium">{t('create_node_title', { type: createOpen.type })}</h2>
            {createOpen.parent && (
              <div className="mb-3 text-xs text-fg-muted">{t('create_node_under', { parent: createOpen.parent.title })}</div>
            )}
            {createError && <div className="mb-3 rounded border border-st-cancelled/40 bg-st-cancelled/10 p-2 text-xs text-st-cancelled">{createError}</div>}
            <input className="input mb-2 w-full" placeholder={t('placeholder_title')} value={createForm.title} onChange={e => setCreateForm({ ...createForm, title: e.target.value })} />
            <textarea className="input mb-2 w-full" rows={3} placeholder={t('placeholder_description')} value={createForm.description} onChange={e => setCreateForm({ ...createForm, description: e.target.value })} />
            <textarea className="input mb-2 w-full" rows={2} placeholder={t('placeholder_acceptance')} value={createForm.acceptance_criteria} onChange={e => setCreateForm({ ...createForm, acceptance_criteria: e.target.value })} />
            <select className="input mb-2 w-full" value={createForm.priority} onChange={e => setCreateForm({ ...createForm, priority: e.target.value })}>
              {['low', 'medium', 'high', 'critical'].map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <input className="input mb-3 w-full" placeholder={t('placeholder_reason')} value={createForm.reason} onChange={e => setCreateForm({ ...createForm, reason: e.target.value })} />
            <div className="flex gap-2">
              <button className="btn-primary" onClick={submitCreate}>{t('btn_create')}</button>
              <button className="btn" onClick={() => setCreateOpen(null)}>{t('btn_cancel')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function NodeRow({ node, depth, expanded, toggle, selected, onSelect, openCreate, matchesFilter, t }: any) {
  const isExpanded = expanded.has(node.id)
  const hasChildren = (node.children || []).length > 0
  const visible = matchesFilter(node)
  const anyDescendantMatches = (n: any): boolean => {
    if (matchesFilter(n) && n.id !== node.id) return true
    return (n.children || []).some(anyDescendantMatches)
  }
  if (!visible && !anyDescendantMatches(node)) return null

  const isSelected = selected === node.id
  const indent = depth * 24

  let icon
  if (node.node_type === 'part') icon = <Folder size={16} className="text-st-in_progress" />
  else if (node.node_type === 'phase') icon = <Layers size={16} className="text-st-review" />
  else icon = <FileCheck2 size={16} className="text-fg-muted" />

  let textSize = 'text-sm'
  if (node.node_type === 'part') textSize = 'text-base font-semibold'
  if (node.node_type === 'phase') textSize = 'text-sm font-medium'

  return (
    <>
      <div
        className={`flex items-center gap-2 rounded px-2 py-1.5 hover:bg-bg-card ${isSelected ? 'bg-bg-card ring-1 ring-st-in_progress' : ''} ${visible ? '' : 'opacity-40'}`}
        style={{ paddingLeft: indent + 8 }}
      >
        <button onClick={() => toggle(node.id)} className="text-fg-dim hover:text-fg" disabled={!hasChildren}>
          {hasChildren ? (isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />) : <span className="inline-block w-3.5" />}
        </button>
        {icon}
        <button className={`flex-1 truncate text-left ${textSize}`} onClick={() => onSelect(node.id)}>
          {node.title}
        </button>
        <StatusBadge status={node.status} />
        <PriorityBadge priority={node.priority} />
        <div className="w-32"><ProgressBar value={node.progress || 0} /></div>
        <span className="ml-2 w-12 text-right font-mono text-xs text-fg-muted">{Math.round(node.progress || 0)}%</span>
        {node.node_type === 'part' && (
          <button title={t('add_phase')} className="btn px-1.5 py-1 text-xs" onClick={() => openCreate(node, 'phase')}>
            <Plus size={12} />
          </button>
        )}
        {node.node_type === 'phase' && (
          <button title={t('add_step')} className="btn px-1.5 py-1 text-xs" onClick={() => openCreate(node, 'step')}>
            <Plus size={12} />
          </button>
        )}
      </div>
      {isExpanded && (node.children || []).map((child: any) => (
        <NodeRow
          key={child.id}
          node={child}
          depth={depth + 1}
          expanded={expanded}
          toggle={toggle}
          selected={selected}
          onSelect={onSelect}
          openCreate={openCreate}
          matchesFilter={matchesFilter}
          t={t}
        />
      ))}
    </>
  )
}
