export interface Instrument {
  canonical_id: string;
  display_symbol: string;
  asset_class: string;
  tradable: boolean;
}

export interface Recommendation {
  id: string;
  canonical_id: string;
  timeframe: string;
  direction: string;
  analytical_bias: string;
  plan_type: string;
  execution_status: string;
  fill_rule: string;
  entry_zone_low: number;
  entry_zone_high: number;
  preferred_entry: number;
  stop_loss: number;
  take_profits: Array<{ price: number; label?: string }>;
  invalidation_rule: string;
  activation_rule?: string;
  activation_condition?: string;
  validity_candles: number;
  analysis_mode: string;
  confidence_label: string;
  similar_past_cases: Record<string, unknown>;
  gate_results: Record<string, unknown>;
  created_at?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  artifacts?: Array<{ type: string; data: Record<string, unknown> }>;
  analysis_mode?: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  title?: string;
  created_at: string;
}

export interface BrokerAccount {
  id: string;
  name: string;
  account_type: string;
  is_connected: boolean;
  broker_server: string;
}

export interface Bot {
  id: string;
  name: string;
  canonical_id: string;
  timeframe: string;
  state: string;
  is_running: boolean;
  active_version_id?: string;
}

export interface Execution {
  id: string;
  canonical_id: string;
  direction: string;
  lot_size: number;
  status: string;
  is_demo: boolean;
  created_at: string;
}

export interface OperatorSettings {
  language: string;
  theme: string;
  risk_per_trade_r: number;
  spread_limit_pips: number;
  daily_loss_limit_r: number;
  consecutive_loss_limit: number;
  price_divergence_threshold_pct: number;
  exposure_cap_r: number;
  live_promotion_confirmation_method: string;
  notification_prefs: Record<string, unknown>;
  emergency_halt: boolean;
  feed_health: Record<string, unknown>;
}

export interface FeedHealth {
  healthy?: boolean;
  oanda?: number;
  twelve_data?: number;
  divergence_pct?: number;
}

export interface WatchlistItem {
  canonical_id: string;
  price?: {
    bid?: number;
    ask?: number;
    mid?: number;
    spread?: number;
  };
}

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export type AnalysisMode = 'quick_scan' | 'deep_analysis';

export interface AgentLogEntry {
  role?: string;
  content?: string;
  tool?: string;
  [key: string]: unknown;
}
