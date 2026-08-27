# Database Schema Reference

## Core Tables

### instruments
OANDA catalog cache. `canonical_id` (PK), `display_symbol`, `asset_class`, `tradable`.

### recommendations
Full recommendation data model with separate `analytical_bias`, `plan_type`, `execution_status`. Never stores WAIT as direction.

### executions
**Separate from recommendations.** Real broker fills only. Links to recommendation_id or bot_id.

### broker_accounts / broker_symbol_aliases
MetaApi accounts and canonical → execution_symbol mapping per account.

### bots / strategies / strategy_versions
Versioned bot definitions. Live bot runs `active_version_id` until operator activates new version.

### trade_rationales
MIND output for every bot fill — rules fired, snapshot, why this bar.

### agent_run_logs
Full multi-agent transcript (hidden from user by default).

### agent_memory
pgvector embeddings of closed recommendations for similar-case recall.

### chat_sessions / chat_messages
Chat history with CopilotKit artifacts inline.

### backtest_runs
Results with mandatory cost model (spread + slippage).

### operator_settings
Single-row settings: language, theme, risk limits, emergency_halt flag.

### performance_reviews
Auto-generated weekly/monthly summaries.

## Extensions

- `vector` — pgvector for semantic memory (1536-dim embeddings)
