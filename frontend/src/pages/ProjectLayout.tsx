import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useParams } from 'react-router-dom'
import { ArrowLeft, GitBranch, Bot, Clock } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { StatusBadge, ProgressBar } from '../components/StatusBadge'

export default function ProjectLayout() {
  const { id } = useParams()
  const { t } = useTranslation()
  const [project, setProject] = useState<any>(null)
  const [tree, setTree] = useState<any>(null)

  const reload = () => {
    if (!id) return
    api.getProject(id).then(setProject)
    api.getTree(id).then(setTree)
  }
  useEffect(() => {
    reload()
    const timer = setInterval(reload, 3000)
    return () => clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  if (!project) return <div className="p-8">{t('loading')}</div>

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-border bg-bg-subtle px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-fg-muted hover:text-fg">
              <ArrowLeft size={18} />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-semibold">{project.name}</h1>
                <StatusBadge status={project.status} />
              </div>
              <div className="flex items-center gap-3 text-xs text-fg-muted">
                {project.local_path && (
                  <span className="font-mono">{project.local_path}</span>
                )}
                {project.repo_url && (
                  <span className="flex items-center gap-1"><GitBranch size={12} />{project.repo_url}</span>
                )}
                {project.active_agent && (
                  <span className="flex items-center gap-1"><Bot size={12} />{project.active_agent}</span>
                )}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="font-mono text-2xl font-bold">{Math.round(project.progress || 0)}%</div>
            <div className="text-xs text-fg-dim">{t('steps_progress', { done: tree?.stats?.done_steps || 0, total: tree?.stats?.steps || 0 })}</div>
          </div>
        </div>
        <div className="mt-3">
          <ProgressBar value={project.progress || 0} color="#22C55E" />
        </div>
        {project.current_focus_node_id && (
          <div className="mt-2 flex items-center gap-2 text-xs">
            <span className="text-fg-dim">{t('focus_label')}</span>
            <FocusBadge nodeId={project.current_focus_node_id} />
          </div>
        )}
      </header>

      <nav className="flex border-b border-border bg-bg-subtle">
        {[
          { to: '', label: t('tab_overview'), end: true },
          { to: 'tree', label: t('tab_tree') },
          { to: 'checkpoints', label: t('tab_checkpoints') },
          { to: 'activity', label: t('tab_activity') },
        ].map(tab => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.end}
            className={({ isActive }) =>
              `px-4 py-2 text-sm ${isActive ? 'border-b-2 border-st-in_progress text-fg' : 'text-fg-muted hover:text-fg'}`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>

      <main className="flex-1 overflow-auto">
        <Outlet context={{ project, tree, reload }} />
      </main>
    </div>
  )
}

function FocusBadge({ nodeId }: { nodeId: string }) {
  const [node, setNode] = useState<any>(null)
  useEffect(() => {
    api.getNode(nodeId).then(setNode).catch(() => {})
  }, [nodeId])
  if (!node) return <span className="text-fg-dim">{nodeId}</span>
  return (
    <span className="flex items-center gap-2">
      <Clock size={12} />
      <span>{node.title}</span>
      <StatusBadge status={node.status} />
    </span>
  )
}
