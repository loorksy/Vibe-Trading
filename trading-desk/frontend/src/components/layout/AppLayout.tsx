import { Outlet } from 'react-router-dom';
import { useUiStore } from '@/stores/uiStore';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';
import { Disclaimer } from '@/components/common/Disclaimer';
import { FeedHealthBanner } from '@/components/common/FeedHealthBanner';
import { EmergencyKillSwitch } from '@/components/common/EmergencyKillSwitch';
import { ConnectBrokerModal } from '@/components/modals/ConnectBrokerModal';
import { SymbolPickerModal } from '@/components/modals/SymbolPickerModal';
import { ExecuteTradeModal } from '@/components/modals/ExecuteTradeModal';
import { EmergencyKillSwitchModal } from '@/components/modals/EmergencyKillSwitchModal';

export function AppLayout() {
  const sidebarOpen = useUiStore((s) => s.sidebarOpen);
  const setSidebarOpen = useUiStore((s) => s.setSidebarOpen);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop sidebar */}
      <aside className="hidden w-56 shrink-0 border-e border-gray-700/50 bg-surface-raised lg:block">
        <Sidebar />
      </aside>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="fixed inset-y-0 start-0 z-50 w-64 border-e border-gray-700/50 bg-surface-raised lg:hidden">
            <Sidebar onNavigate={() => setSidebarOpen(false)} />
          </aside>
        </>
      )}

      <div className="flex flex-1 flex-col overflow-hidden">
        <FeedHealthBanner />
        <Navbar />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
        <Disclaimer />
      </div>

      <EmergencyKillSwitch />
      <ConnectBrokerModal />
      <SymbolPickerModal />
      <ExecuteTradeModal />
      <EmergencyKillSwitchModal />
    </div>
  );
}
