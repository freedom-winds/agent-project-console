import { Routes, Route, NavLink } from 'react-router-dom'
import { FolderKanban, Settings as SettingsIcon } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import ProjectListPage from './pages/ProjectListPage'
import ProjectLayout from './pages/ProjectLayout'
import OverviewPage from './pages/OverviewPage'
import TaskTreePage from './pages/TaskTreePage'
import CheckpointsPage from './pages/CheckpointsPage'
import ActivityPage from './pages/ActivityPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  const { t, i18n } = useTranslation()
  const isZh = i18n.language === 'zh'

  return (
    <div className="flex h-full">
      <nav className="w-60 shrink-0 border-r border-border bg-bg-subtle px-3 py-4">
        <div className="mb-6 px-2">
          <div className="text-base font-semibold">Agent Project Console</div>
          <div className="text-xs text-fg-dim">{t('nav_local')}</div>
        </div>
        <NavItem to="/" icon={<FolderKanban size={16} />}>{t('nav_projects')}</NavItem>
        <NavItem to="/settings" icon={<SettingsIcon size={16} />}>{t('nav_settings')}</NavItem>

        <div className="absolute bottom-4 left-3 flex items-center gap-1">
          <button
            className={`rounded px-2 py-1 text-xs ${isZh ? 'bg-bg-card text-fg' : 'text-fg-dim hover:text-fg'}`}
            onClick={() => i18n.changeLanguage('zh')}
          >
            中文
          </button>
          <span className="text-fg-dim text-xs">·</span>
          <button
            className={`rounded px-2 py-1 text-xs ${!isZh ? 'bg-bg-card text-fg' : 'text-fg-dim hover:text-fg'}`}
            onClick={() => i18n.changeLanguage('en')}
          >
            EN
          </button>
        </div>
      </nav>
      <div className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<ProjectListPage />} />
          <Route path="/projects/:id" element={<ProjectLayout />}>
            <Route index element={<OverviewPage />} />
            <Route path="tree" element={<TaskTreePage />} />
            <Route path="checkpoints" element={<CheckpointsPage />} />
            <Route path="activity" element={<ActivityPage />} />
          </Route>
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<div className="p-8 text-fg-dim">{t('page_not_found')}</div>} />
        </Routes>
      </div>
    </div>
  )
}

function NavItem({ to, icon, children }: { to: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) =>
        `flex items-center gap-2 rounded px-3 py-2 text-sm ${isActive ? 'bg-bg-card text-fg' : 'text-fg-muted hover:bg-bg-card hover:text-fg'}`
      }
    >
      {icon}
      {children}
    </NavLink>
  )
}
