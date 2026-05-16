// REST API client (talks to /api/*)

const BASE = ''

async function call(path: string, init?: RequestInit) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) {
    let msg = res.statusText
    try {
      const j = await res.json()
      msg = j.message || j.error || msg
    } catch {}
    throw new Error(msg)
  }
  if (res.status === 204) return null
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return res.json()
  return res.text()
}

export const api = {
  health: () => call('/api/health'),

  listProjects: () => call('/api/projects'),
  getProject: (id: string) => call(`/api/projects/${id}`),
  createProject: (data: any) => call('/api/projects', { method: 'POST', body: JSON.stringify(data) }),
  patchProject: (id: string, data: any) => call(`/api/projects/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  getTree: (id: string) => call(`/api/projects/${id}/tree`),
  setFocus: (id: string, node_id: string, reason = '') => call(`/api/projects/${id}/focus`, { method: 'POST', body: JSON.stringify({ node_id, reason }) }),
  search: (id: string, q = '') => call(`/api/projects/${id}/search?q=${encodeURIComponent(q)}`),

  createNode: (data: any) => call('/api/nodes', { method: 'POST', body: JSON.stringify(data) }),
  getNode: (id: string) => call(`/api/nodes/${id}`),
  patchNode: (id: string, data: any) => call(`/api/nodes/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteNode: (id: string, reason: string) => call(`/api/nodes/${id}?reason=${encodeURIComponent(reason)}`, { method: 'DELETE' }),
  updateStatus: (id: string, data: any) => call(`/api/nodes/${id}/status`, { method: 'POST', body: JSON.stringify(data) }),
  addEvidence: (id: string, data: any) => call(`/api/nodes/${id}/evidence`, { method: 'POST', body: JSON.stringify(data) }),
  listEvidence: (id: string) => call(`/api/nodes/${id}/evidence`),
  addArtifact: (id: string, data: any) => call(`/api/nodes/${id}/artifacts`, { method: 'POST', body: JSON.stringify(data) }),
  listArtifacts: (id: string) => call(`/api/nodes/${id}/artifacts`),

  listActivity: (pid: string, limit = 200) => call(`/api/projects/${pid}/activity?limit=${limit}`),
  listCheckpoints: (pid: string) => call(`/api/projects/${pid}/checkpoints`),
  createCheckpoint: (pid: string, data: any) => call(`/api/projects/${pid}/checkpoints`, { method: 'POST', body: JSON.stringify(data) }),

  listTokens: () => call('/api/settings/tokens'),
  createToken: (name: string, scopes?: string[]) => call('/api/settings/tokens', { method: 'POST', body: JSON.stringify({ name, scopes }) }),
  revokeToken: (id: string) => call(`/api/settings/tokens/${id}`, { method: 'DELETE' }),
}

export type StatusKind = 'planned' | 'ready' | 'in_progress' | 'blocked' | 'review' | 'done' | 'skipped' | 'cancelled'

export const STATUS_CN: Record<StatusKind, string> = {
  planned: '已规划',
  ready: '可开始',
  in_progress: '进行中',
  blocked: '阻塞',
  review: '待审核',
  done: '完成',
  skipped: '跳过',
  cancelled: '取消',
}

export const STATUS_COLOR: Record<StatusKind, string> = {
  planned: 'bg-st-planned/20 text-st-planned border border-st-planned/40',
  ready: 'bg-st-ready/20 text-st-ready border border-st-ready/40',
  in_progress: 'bg-st-in_progress/20 text-st-in_progress border border-st-in_progress/40',
  blocked: 'bg-st-blocked/20 text-st-blocked border border-st-blocked/40',
  review: 'bg-st-review/20 text-st-review border border-st-review/40',
  done: 'bg-st-done/20 text-st-done border border-st-done/40',
  skipped: 'bg-st-skipped/20 text-st-skipped border border-st-skipped/40',
  cancelled: 'bg-st-cancelled/20 text-st-cancelled border border-st-cancelled/40',
}
