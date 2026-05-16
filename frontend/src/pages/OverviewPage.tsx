import { useEffect, useState } from 'react'
import { useOutletContext, Link, useParams } from 'react-router-dom'
import { Activity as ActivityIcon, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react'
import { api } from '../api'
import { ProgressBar, StatusBadge } from '../components/StatusBadge'

interface Ctx {
  project: any
  tree: any
  reload: () => void
}

export default function OverviewPage() {
  const { project, tree } = useOutletContext<Ctx>()
  const { id } = useParams()
  const [activity, setActivity] = useState<any[]>([])
  const [checkpoints, setCheckpoints] = useState<any[]>([])

  useEffect(() => {
    if (!id) return
    api.listActivity(id, 20).then(d => setActivity(d.activities || []))
    api.listCheckpoints(id).then(d => setCheckpoints(d.checkpoints || []))
  }, [id, project?.updated_at])

  const allNodes: any[] = []
  const walk = (nodes: any[]) => nodes.forEach(n => { allNodes.push(n); walk(n.children || []) })
  if (tree?.tree) walk(tree.tree)
  const inProgress = allNodes.filter(n => n.node_type === 'step' && n.status === 'in_progress')
  const blocked = allNodes.filter(n => n.node_type === 'step' && n.status === 'blocked')
  const review = allNodes.filter(n => n.node_type === 'step' && n.status === 'review')
  const parts = (tree?.tree || []).filter((n: any) => n.node_type === 'part')

  return (
    <div className="grid gap-6 p-6 lg:grid-cols-3">
      <div className="lg:col-span-2 space-y-6">
        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatCard icon={<Loader2 size={18} className="text-st-in_progress" />} label="进行中" value={inProgress.length} color="text-st-in_progress" />
          <StatCard icon={<CheckCircle2 size={18} className="text-st-done" />} label="已完成" value={tree?.stats?.done_steps || 0} color="text-st-done" />
          <StatCard icon={<AlertTriangle size={18} className="text-st-blocked" />} label="阻塞" value={blocked.length} color="text-st-blocked" />
          <StatCard icon={<ActivityIcon size={18} className="text-st-review" />} label="待审核" value={review.length} color="text-st-review" />
        </div>

        {/* Part progress overview */}
        <div className="card p-4">
          <h2 className="mb-3 text-base font-semibold">Part Progress</h2>
          {parts.length === 0 ? (
            <div className="text-sm text-fg-dim">No Parts yet. Use MCP create_node or the Tree page.</div>
          ) : (
            <div className="space-y-3">
              {parts.map((p: any) => (
                <div key={p.id}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <Link to={`/projects/${id}/tree`} className="font-medium hover:text-st-in_progress">{p.title}</Link>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={p.status} />
                      <span className="font-mono text-xs">{Math.round(p.progress || 0)}%</span>
                    </div>
                  </div>
                  <ProgressBar value={p.progress || 0} color={progressColor(p.status)} />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* In progress and blocked */}
        <div className="grid gap-4 md:grid-cols-2">
          <div className="card p-4">
            <h2 className="mb-3 text-base font-semibold">In Progress</h2>
            {inProgress.length === 0 ? (
              <div className="text-sm text-fg-dim">No steps in progress.</div>
            ) : (
              <div className="space-y-2">
                {inProgress.map(s => (
                  <Link key={s.id} to={`/projects/${id}/tree?step=${s.id}`} className="block rounded border border-border p-2 hover:border-st-in_progress">
                    <div className="text-sm font-medium">{s.title}</div>
                    <ProgressBar value={s.progress || 0} />
                  </Link>
                ))}
              </div>
            )}
          </div>

          <div className="card p-4">
            <h2 className="mb-3 text-base font-semibold flex items-center gap-2 text-st-blocked"><AlertTriangle size={16} /> Blockers</h2>
            {blocked.length === 0 ? (
              <div className="text-sm text-fg-dim">No blockers.</div>
            ) : (
              <div className="space-y-2">
                {blocked.map(s => (
                  <Link key={s.id} to={`/projects/${id}/tree?step=${s.id}`} className="block rounded border border-st-blocked/40 bg-st-blocked/5 p-2">
                    <div className="text-sm font-medium">{s.title}</div>
                    {s.blocker_reason && <div className="text-xs text-fg-muted">{s.blocker_reason}</div>}
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right: recent activity & checkpoints */}
      <div className="space-y-6">
        <div className="card p-4">
          <h2 className="mb-3 text-base font-semibold">Recent Activity</h2>
          <div className="space-y-2">
            {activity.length === 0 ? (
              <div className="text-sm text-fg-dim">No activity yet.</div>
            ) : (
              activity.slice(0, 10).map(a => (
                <div key={a.id} className="text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-st-in_progress">{a.action_type}</span>
                    <span className="text-fg-dim">{new Date(a.created_at).toLocaleTimeString()}</span>
                  </div>
                  <div className="text-fg-muted">by {a.actor}</div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="card p-4">
          <h2 className="mb-3 text-base font-semibold">Recent Checkpoints</h2>
          {checkpoints.length === 0 ? (
            <div className="text-sm text-fg-dim">No checkpoints yet.</div>
          ) : (
            <div className="space-y-3">
              {checkpoints.slice(0, 5).map(cp => (
                <Link key={cp.id} to={`/projects/${id}/checkpoints`} className="block rounded border border-border p-2 text-xs hover:border-st-in_progress">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{cp.agent_name}</span>
                    <span className="text-fg-dim">{new Date(cp.created_at).toLocaleString()}</span>
                  </div>
                  {cp.summary && <div className="mt-1 text-fg-muted">{cp.summary}</div>}
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, color }: any) {
  return (
    <div className="card p-3">
      <div className="mb-1 flex items-center gap-2 text-xs text-fg-muted">{icon}<span>{label}</span></div>
      <div className={`font-mono text-2xl font-bold ${color}`}>{value}</div>
    </div>
  )
}

function progressColor(status: string) {
  if (status === 'done') return '#22C55E'
  if (status === 'blocked') return '#F97316'
  if (status === 'review') return '#A78BFA'
  return '#60A5FA'
}
