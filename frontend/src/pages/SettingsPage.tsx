import { useEffect, useState } from 'react'
import { Copy, Plus, Trash2 } from 'lucide-react'
import { api } from '../api'

const ALL_SCOPES = [
  'read_project',
  'write_plan',
  'update_status',
  'write_evidence',
  'write_checkpoint',
  'admin',
] as const

export default function SettingsPage() {
  const [tokens, setTokens] = useState<any[]>([])
  const [name, setName] = useState('')
  const [scopes, setScopes] = useState<string[]>([
    'read_project',
    'write_plan',
    'update_status',
    'write_evidence',
    'write_checkpoint',
  ])
  const [newToken, setNewToken] = useState<string | null>(null)
  const [error, setError] = useState('')

  const load = () => api.listTokens().then(d => setTokens(d.tokens || []))
  useEffect(() => { load() }, [])

  const create = async () => {
    setError('')
    try {
      const data = await api.createToken(name || 'mcp', scopes)
      setNewToken(data.token)
      setName('')
      load()
    } catch (e: any) {
      setError(e.message)
    }
  }

  const revoke = async (id: string) => {
    if (!confirm('Revoke this token?')) return
    await api.revokeToken(id)
    load()
  }

  const toggleScope = (s: string) => {
    setScopes(cur => cur.includes(s) ? cur.filter(x => x !== s) : [...cur, s])
  }

  return (
    <div className="h-full overflow-y-auto p-8">
      <h1 className="mb-6 text-2xl font-semibold">Settings</h1>

      <div className="card mb-6 p-5">
        <h2 className="mb-3 text-base font-semibold">MCP Tokens</h2>
        <p className="mb-4 text-sm text-fg-muted">
          Tokens are used by the MCP STDIO server to authenticate against this backend.
          A token is shown only once at creation; copy it immediately.
        </p>

        {error && <div className="mb-3 rounded border border-st-cancelled/40 bg-st-cancelled/10 p-2 text-xs text-st-cancelled">{error}</div>}

        {newToken && (
          <div className="mb-4 rounded border border-st-done/40 bg-st-done/10 p-3 text-sm">
            <div className="mb-2 font-medium text-st-done">Token created. Copy now — it will not be shown again.</div>
            <div className="flex items-center gap-2">
              <code className="flex-1 break-all rounded bg-bg-subtle p-2 font-mono text-xs">{newToken}</code>
              <button className="btn" onClick={() => { navigator.clipboard.writeText(newToken); }}>
                <Copy size={14} /> Copy
              </button>
            </div>
            <button className="mt-2 text-xs text-fg-dim hover:text-fg" onClick={() => setNewToken(null)}>Hide</button>
          </div>
        )}

        <div className="mb-4 grid gap-2 md:grid-cols-2">
          <input className="input" placeholder="Token name (e.g. cline, codex)" value={name} onChange={e => setName(e.target.value)} />
          <div className="flex flex-wrap gap-2">
            {ALL_SCOPES.map(s => (
              <label key={s} className={`badge cursor-pointer ${scopes.includes(s) ? 'bg-st-in_progress/20 text-st-in_progress border border-st-in_progress/40' : 'bg-bg-subtle text-fg-dim border border-border'}`}>
                <input type="checkbox" className="hidden" checked={scopes.includes(s)} onChange={() => toggleScope(s)} />
                {s}
              </label>
            ))}
          </div>
        </div>
        <button className="btn-primary" onClick={create}><Plus size={14} /> Create Token</button>

        <div className="mt-5 space-y-2">
          {tokens.length === 0 ? (
            <div className="text-sm text-fg-dim">No tokens yet.</div>
          ) : (
            tokens.map(t => (
              <div key={t.id} className="flex items-center justify-between rounded border border-border p-3">
                <div>
                  <div className="text-sm font-medium">{t.name}</div>
                  <div className="font-mono text-xs text-fg-dim">{t.token_preview}</div>
                  <div className="text-xs text-fg-dim">scopes: {(t.scopes || []).join(', ') || '—'}</div>
                  <div className="text-xs text-fg-dim">
                    created {t.created_at ? new Date(t.created_at).toLocaleString() : '—'}
                    {t.revoked_at && <span className="ml-2 text-st-cancelled">revoked</span>}
                  </div>
                </div>
                {!t.revoked_at && (
                  <button className="btn text-xs text-st-cancelled" onClick={() => revoke(t.id)}>
                    <Trash2 size={12} /> Revoke
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="card p-5">
        <h2 className="mb-3 text-base font-semibold">MCP Server Snippets</h2>
        <p className="mb-3 text-sm text-fg-muted">Use these in your MCP client configuration. See <code className="font-mono">docs/MCP_SETUP.md</code> for full instructions.</p>
        <pre className="overflow-auto rounded bg-bg-subtle p-3 font-mono text-xs">
{`# Cline / Claude Code / Codex (mcp_servers entry)
{
  "agent-project-console": {
    "command": "python",
    "args": ["-m", "app.mcp.server"],
    "cwd": "<path-to-repo>/agent-project-console/backend",
    "env": {
      "APC_BASE_URL": "http://127.0.0.1:8765",
      "APC_MCP_TOKEN": "<paste your token here>",
      "APC_AGENT_NAME": "cline",
      "PYTHONUTF8": "1",
      "PYTHONIOENCODING": "utf-8"
    }
  }
}`}
        </pre>
      </div>
    </div>
  )
}
