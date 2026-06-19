import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, AlertTriangle } from 'lucide-react'
import { api } from '../api'
import { StatusBadge, ProgressBar } from '../components/StatusBadge'

export default function ProjectListPage() {
  const [projects, setProjects] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', local_path: '', repo_url: '' })
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const reload = () =>
    api.listProjects().then(d => {
      setProjects(d.projects || [])
      setLoading(false)
    })

  useEffect(() => {
    reload()
    const t = setInterval(reload, 3000)
    return () => clearInterval(t)
  }, [])

  const create = async () => {
    setError('')
    if (!form.name.trim()) {
      setError('name required')
      return
    }
    try {
      const proj = await api.createProject(form)
      navigate(`/projects/${proj.id}`)
    } catch (e: any) {
      setError(e.message)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Projects</h1>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={16} /> New Project
        </button>
      </div>

      {showCreate && (
        <div className="card mb-6 p-5">
          <h2 className="mb-4 text-lg font-medium">Create Project</h2>
          {error && <div className="mb-3 rounded border border-st-cancelled/40 bg-st-cancelled/10 p-2 text-sm text-st-cancelled">{error}</div>}
          <div className="grid gap-3 md:grid-cols-2">
            <input className="input md:col-span-2" placeholder="Project name *" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
            <textarea className="input md:col-span-2" rows={2} placeholder="Description" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
            <input className="input" placeholder="Local path (e.g. f:\\projects\\my-app)" value={form.local_path} onChange={e => setForm({ ...form, local_path: e.target.value })} />
            <input className="input" placeholder="Repo URL" value={form.repo_url} onChange={e => setForm({ ...form, repo_url: e.target.value })} />
          </div>
          <div className="mt-4 flex gap-2">
            <button className="btn-primary" onClick={create}>Create</button>
            <button className="btn" onClick={() => setShowCreate(false)}>Cancel</button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-fg-dim">Loading...</div>
      ) : projects.length === 0 ? (
        <div className="card p-8 text-center text-fg-dim">No projects yet. Create your first one.</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map(p => (
            <Link key={p.id} to={`/projects/${p.id}`} className="card p-5 transition hover:border-st-in_progress">
              <div className="mb-2 flex items-start justify-between">
                <h3 className="text-base font-semibold">{p.name}</h3>
                <StatusBadge status={p.status} />
              </div>
              <p className="mb-4 line-clamp-2 min-h-[40px] text-sm text-fg-muted">{p.description || 'No description'}</p>
              <div className="mb-1 flex items-center justify-between text-xs text-fg-muted">
                <span>Progress</span>
                <span className="font-mono">{Math.round(p.progress || 0)}%</span>
              </div>
              <ProgressBar value={p.progress || 0} color="#22C55E" />
              <div className="mt-4 grid grid-cols-4 gap-2 text-xs">
                <Stat label="Parts" value={p.stats?.parts || 0} />
                <Stat label="Phases" value={p.stats?.phases || 0} />
                <Stat label="Steps" value={p.stats?.steps || 0} />
                <Stat label="Done" value={p.stats?.done_steps || 0} />
              </div>
              {(p.stats?.blocked_steps || 0) > 0 && (
                <div className="mt-3 flex items-center gap-1 text-xs text-st-blocked">
                  <AlertTriangle size={12} /> {p.stats.blocked_steps} blocked
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded bg-bg-subtle p-2 text-center">
      <div className="font-mono text-base font-semibold">{value}</div>
      <div className="text-fg-dim">{label}</div>
    </div>
  )
}
