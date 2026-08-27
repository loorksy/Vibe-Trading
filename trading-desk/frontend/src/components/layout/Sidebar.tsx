import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const PRIMARY_NAV = [
  { to: '/', key: 'ask', icon: '💬' },
  { to: '/today', key: 'today', icon: '📊' },
  { to: '/build', key: 'build', icon: '🔧' },
];

const SECONDARY_NAV = [
  { to: '/chart', key: 'chart' },
  { to: '/recommendations', key: 'recommendations' },
  { to: '/watchlist', key: 'watchlist' },
  { to: '/exposure', key: 'exposure' },
  { to: '/account', key: 'account' },
  { to: '/strategies', key: 'strategies' },
  { to: '/demo', key: 'demo' },
  { to: '/bots', key: 'bots' },
  { to: '/memory', key: 'memory' },
  { to: '/review', key: 'review' },
  { to: '/history', key: 'history' },
  { to: '/settings', key: 'settings' },
];

interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const { t } = useTranslation();

  return (
    <nav className="flex h-full flex-col">
      <div className="mb-4 px-3">
        <h1 className="text-lg font-bold text-accent">Trading Desk</h1>
        <p className="text-xs text-gray-500">AI Assistant</p>
      </div>

      <div className="mb-2 px-3">
        <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-600">Daily</p>
        <div className="space-y-1">
          {PRIMARY_NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={onNavigate}
              className={({ isActive }) => (isActive ? 'nav-link-active' : 'nav-link')}
            >
              <span>{item.icon}</span>
              {t(`nav.${item.key}`)}
            </NavLink>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3">
        <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-600">More</p>
        <div className="space-y-1">
          {SECONDARY_NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) => (isActive ? 'nav-link-active' : 'nav-link')}
            >
              {t(`nav.${item.key}`)}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
}
