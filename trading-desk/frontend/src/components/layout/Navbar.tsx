import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/stores/authStore';
import { useUiStore } from '@/stores/uiStore';
import { ThemeToggle } from '@/components/common/ThemeToggle';
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher';
import { SymbolPicker } from '@/components/SymbolPicker';

export function Navbar() {
  const { t } = useTranslation();
  const { username, logout } = useAuthStore();
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-gray-700/50 bg-surface/95 px-4 backdrop-blur">
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="btn-ghost p-2 lg:hidden"
          aria-label="Menu"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <SymbolPicker compact />
      </div>

      <div className="flex items-center gap-2">
        <LanguageSwitcher />
        <ThemeToggle />
        {username && (
          <span className="hidden text-sm text-gray-400 sm:inline">{username}</span>
        )}
        <button onClick={logout} className="btn-ghost text-sm">
          {t('nav.logout')}
        </button>
      </div>
    </header>
  );
}
