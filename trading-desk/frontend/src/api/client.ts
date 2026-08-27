const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function getToken(): string | null {
  return localStorage.getItem('access_token');
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail || res.statusText);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Auth
  login: (username: string, password: string) =>
    request<{ access_token: string; token_type: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  me: () => request<{ username: string }>('/auth/me'),

  // Instruments
  instruments: (q = '') =>
    request<import('@/types').Instrument[]>(`/instruments?q=${encodeURIComponent(q)}`),
  refreshInstruments: () =>
    request<{ refreshed: number }>('/instruments/refresh', { method: 'POST' }),
  candles: (canonicalId: string, timeframe = '1h', count = 500) =>
    request<{ candles: import('@/types').Candle[]; source: string }>(
      `/instruments/${canonicalId}/candles?timeframe=${timeframe}&count=${count}`,
    ),
  price: (canonicalId: string) =>
    request<{ price: Record<string, number>; feed_health: import('@/types').FeedHealth }>(
      `/instruments/${canonicalId}/price`,
    ),

  // Chat
  sendMessage: (body: {
    session_id?: string;
    message: string;
    mode: string;
    canonical_id?: string;
    timeframe?: string;
  }) =>
    request<{
      session_id: string;
      message: string;
      artifacts?: Array<{ type: string; data: Record<string, unknown> }>;
      transcript_available: boolean;
    }>('/chat/message', { method: 'POST', body: JSON.stringify(body) }),
  chatSessions: () => request<import('@/types').ChatSession[]>('/chat/sessions'),
  chatMessages: (sessionId: string) =>
    request<import('@/types').ChatMessage[]>(`/chat/sessions/${sessionId}/messages`),
  agentLog: (sessionId: string) =>
    request<{ transcript: import('@/types').AgentLogEntry[]; gate_results?: unknown }>(
      `/chat/sessions/${sessionId}/agent-log`,
    ),

  // Recommendations
  recommendations: () => request<import('@/types').Recommendation[]>('/recommendations'),
  recommendation: (id: string) =>
    request<import('@/types').Recommendation>(`/recommendations/${id}`),
  analyzeRecommendation: (body: {
    canonical_id: string;
    timeframe: string;
    mode: string;
  }) =>
    request<{ published: boolean; recommendation?: import('@/types').Recommendation; error?: string }>(
      '/recommendations/analyze',
      { method: 'POST', body: JSON.stringify(body) },
    ),
  convertToBot: (recId: string) =>
    request<{ bot_id: string; strategy_id: string }>(
      `/recommendations/${recId}/convert-bot`,
      { method: 'POST' },
    ),

  // Account
  connectBroker: (body: {
    name: string;
    account_type: string;
    metaapi_account_id: string;
    broker_server: string;
    token: string;
  }) =>
    request<{ id: string; connected: boolean }>('/account/connect', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  accounts: () => request<import('@/types').BrokerAccount[]>('/account/accounts'),
  saveAlias: (body: {
    account_id: string;
    canonical_id: string;
    execution_symbol: string;
  }) =>
    request<{ id: string; verified: boolean }>('/account/aliases', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  aliases: (accountId: string) =>
    request<Array<{ canonical_id: string; execution_symbol: string; verified: boolean }>>(
      `/account/aliases/${accountId}`,
    ),

  // Executions
  executeTrade: (body: {
    recommendation_id: string;
    account_id: string;
    lot_size: number;
  }) =>
    request<{ execution_id: string; result: Record<string, unknown> }>('/executions', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  executions: () => request<import('@/types').Execution[]>('/executions'),

  // Bots
  bots: () => request<import('@/types').Bot[]>('/bots'),
  activateBot: (
    botId: string,
    body: {
      bot_id: string;
      canonical_id: string;
      timeframe: string;
      account_id: string;
      risk_per_trade_r?: number;
      spread_limit_pips?: number;
      open_position_cap?: number;
    },
  ) =>
    request<{ id: string; is_running: boolean }>(`/bots/${botId}/activate`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  stopBot: (botId: string) =>
    request<{ id: string; is_running: boolean }>(`/bots/${botId}/stop`, { method: 'POST' }),
  stopAllBots: () =>
    request<{ halted: boolean; bots_stopped: boolean }>('/bots/stop-all', { method: 'POST' }),
  promoteLive: (botId: string, confirmation: string) =>
    request<{ id: string; state: string }>(`/bots/${botId}/promote-live`, {
      method: 'POST',
      body: JSON.stringify({ bot_id: botId, confirmation }),
    }),

  // Platform
  settings: () => request<import('@/types').OperatorSettings>('/settings'),
  updateSettings: (body: Partial<import('@/types').OperatorSettings>) =>
    request<{ updated: boolean }>('/settings', {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  watchlist: () => request<import('@/types').WatchlistItem[]>('/watchlist'),
  addWatchlist: (canonical_id: string) =>
    request<{ added: string }>('/watchlist', {
      method: 'POST',
      body: JSON.stringify({ canonical_id }),
    }),
  removeWatchlist: (canonicalId: string) =>
    request<{ removed: string }>(`/watchlist/${canonicalId}`, { method: 'DELETE' }),
  today: (benchmark = 'XAU_USD') =>
    request<{
      news: Array<Record<string, unknown>>;
      calendar: Array<Record<string, unknown>>;
      feed_health: import('@/types').FeedHealth;
      benchmark: string;
      disclaimer: string;
    }>(`/today?benchmark=${benchmark}`),
  exposure: () => request<Record<string, unknown>>('/exposure'),
  backtest: (body: {
    strategy_version_id: string;
    canonical_id: string;
    timeframe: string;
    start_date: string;
    end_date: string;
  }) =>
    request<{ id: string; results: Record<string, unknown> }>('/backtests', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  memoryLessons: () =>
    request<Array<{ id: string; lesson: string; canonical_id: string }>>('/memory/lessons'),
  reviews: () =>
    request<Array<{ id: string; period_type: string; summary: string }>>('/review'),

  // Health
  health: () =>
    request<{ status: string; checks: Record<string, string | boolean> }>('/health'),
};

export { ApiError };
