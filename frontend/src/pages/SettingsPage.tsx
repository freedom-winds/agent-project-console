import { useEffect, useState } from 'react'
import { Copy, Plus, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
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
  const { t } = useTranslation()

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
    if (!confirm(t('confirm_revoke'))) return
    await api.revokeToken(id)
    load()
  }

  const toggleScope = (s: string) => {
    setScopes(cur => cur.includes(s) ? cur.filter(x => x !== s) : [...cur, s])
  }

  return (
    <div className="h-full overflow-y-auto p-8">
      <h1 className="mb-6 text-2xl font-semibold">{t('settings_title')}</h1>

      <div className="card mb-6 p-5">
        <h2 className="mb-3 text-base font-semibold">{t('mcp_tokens_title')}</h2>
        <p className="mb-4 text-sm text-fg-muted">{t('mcp_tokens_desc')}</p>

        {error && <div className="mb-3 rounded border border-st-cancelled/40 bg-st-cancelled/10 p-2 text-xs text-st-cancelled">{error}</div>}

        {newToken && (
          <div className="mb-4 rounded border border-st-done/40 bg-st-done/10 p-3 text-sm">
            <div className="mb-2 font-medium text-st-done">{t('token_created_msg')}</div>
            <div className="flex items-center gap-2">
              <code className="flex-1 break-all rounded bg-bg-subtle p-2 font-mono text-xs">{newToken}</code>
              <button className="btn" onClick={() => { navigator.clipboard.writeText(newToken) }}>
                <Copy size={14} /> {t('btn_copy')}
              </button>
            </div>
            <button className="mt-2 text-xs text-fg-dim hover:text-fg" onClick={() => setNewToken(null)}>{t('btn_hide')}</button>
          </div>
        )}

        <div className="mb-4 grid gap-2 md:grid-cols-2">
          <input className="input" placeholder={t('placeholder_token_name')} value={name} onChange={e => setName(e.target.value)} />
          <div className="flex flex-wrap gap-2">
            {ALL_SCOPES.map(s => (
              <label key={s} className={`badge cursor-pointer ${scopes.includes(s) ? 'bg-st-in_progress/20 text-st-in_progress border border-st-in_progress/40' : 'bg-bg-subtle text-fg-dim border border-border'}`}>
                <input type="checkbox" className="hidden" checked={scopes.includes(s)} onChange={() => toggleScope(s)} />
                {s}
              </label>
            ))}
          </div>
        </div>
        <button className="btn-primary" onClick={create}><Plus size={14} /> {t('btn_create_token')}</button>

        <div className="mt-5 space-y-2">
          {tokens.length === 0 ? (
            <div className="text-sm text-fg-dim">{t('no_tokens')}</div>
          ) : (
            tokens.map(tok => (
              <div key={tok.id} className="flex items-center justify-between rounded border border-border p-3">
                <div>
                  <div className="text-sm font-medium">{tok.name}</div>
                  <div className="font-mono text-xs text-fg-dim">{tok.token_preview}</div>
                  <div className="text-xs text-fg-dim">{t('token_scopes', { scopes: (tok.scopes || []).join(', ') || '—' })}</div>
                  <div className="text-xs text-fg-dim">
                    {tok.created_at ? t('token_created_at', { date: new Date(tok.created_at).toLocaleString() }) : '—'}
                    {tok.revoked_at && <span className="ml-2 text-st-cancelled">{t('token_revoked')}</span>}
                  </div>
                </div>
                {!tok.revoked_at && (
                  <button className="btn text-xs text-st-cancelled" onClick={() => revoke(tok.id)}>
                    <Trash2 size={12} /> {t('btn_revoke')}
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="card p-5">
        <h2 className="mb-3 text-base font-semibold">{t('mcp_snippets_title')}</h2>
        <p className="mb-3 text-sm text-fg-muted">{t('mcp_snippets_desc')}</p>
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
