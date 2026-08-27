import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { AppLayout } from '@/components/layout/AppLayout';
import { LoginPage } from '@/pages/LoginPage';
import { AskPage } from '@/pages/AskPage';
import { TodayPage } from '@/pages/TodayPage';
import { BuildPage } from '@/pages/BuildPage';
import { ChartPage } from '@/pages/ChartPage';
import { RecommendationsPage } from '@/pages/RecommendationsPage';
import { RecommendationDetailPage } from '@/pages/RecommendationDetailPage';
import { WatchlistPage } from '@/pages/WatchlistPage';
import { ExposurePage } from '@/pages/ExposurePage';
import { AccountPage } from '@/pages/AccountPage';
import { StrategiesPage } from '@/pages/StrategiesPage';
import { StrategyNewPage } from '@/pages/StrategyNewPage';
import { StrategyOptimizePage } from '@/pages/StrategyOptimizePage';
import { StrategyVersionsPage } from '@/pages/StrategyVersionsPage';
import { DemoPage } from '@/pages/DemoPage';
import { BotsPage } from '@/pages/BotsPage';
import { BotDetailPage } from '@/pages/BotDetailPage';
import { BotLivePage } from '@/pages/BotLivePage';
import { MemoryPage } from '@/pages/MemoryPage';
import { ReviewPage } from '@/pages/ReviewPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { HistoryPage } from '@/pages/HistoryPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<AskPage />} />
        <Route path="today" element={<TodayPage />} />
        <Route path="build" element={<BuildPage />} />
        <Route path="chart" element={<ChartPage />} />
        <Route path="chart/:symbol" element={<ChartPage />} />
        <Route path="recommendations" element={<RecommendationsPage />} />
        <Route path="recommendations/:id" element={<RecommendationDetailPage />} />
        <Route path="watchlist" element={<WatchlistPage />} />
        <Route path="exposure" element={<ExposurePage />} />
        <Route path="account" element={<AccountPage />} />
        <Route path="strategies" element={<StrategiesPage />} />
        <Route path="strategies/new" element={<StrategyNewPage />} />
        <Route path="strategies/:id/optimize" element={<StrategyOptimizePage />} />
        <Route path="strategies/:id/versions" element={<StrategyVersionsPage />} />
        <Route path="demo" element={<DemoPage />} />
        <Route path="bots" element={<BotsPage />} />
        <Route path="bots/:id" element={<BotDetailPage />} />
        <Route path="bots/:id/live" element={<BotLivePage />} />
        <Route path="memory" element={<MemoryPage />} />
        <Route path="review" element={<ReviewPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="history" element={<HistoryPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
