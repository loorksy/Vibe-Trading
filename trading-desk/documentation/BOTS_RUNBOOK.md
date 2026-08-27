# Bots Layer Runbook

## CODE + MIND Loop

Every bot signal follows this sequence:

1. **CODE** — versioned Python strategy evaluates rules on scheduled bar
2. **Gates** — 10 bot-specific safety checks (session, news, spread, alias, etc.)
3. **MIND** — Bot Rationale Writer produces structured "why now"
4. **Order** — MetaApi with SL attached, using `execution_symbol`
5. **Store** — rationale linked to execution row

If rationale generation fails → NO ORDER.

## Demo → Live Promotion

1. Bot must have successful demo run on same canonical symbol/timeframe
2. Operator reviews demo results in Promote-to-Live modal
3. Extra confirmation: type exact canonical symbol OR enter PIN
4. Live orders require mapped broker alias

## Versioning

- Every code change creates new `strategy_versions` row
- Live bot keeps running `active_version_id` until operator activates new version
- One-click rollback to any previous version

## Emergency Kill Switch

- `POST /api/bots/stop-all` — stops all bots, sets `emergency_halt` flag
- Telegram `/stopall` — same effect
- Accessible from any page in the UI

## Bot Safety Gates (every decision)

1. Trading session open
2. No high-impact news in block window
3. Spread within limit
4. No duplicate position (unless rules allow)
5. Stop-loss attached
6. Daily-loss / consecutive-loss caps
7. Portfolio exposure warning (blocks only if cap configured)
8. Broker alias exists
9. Rationale written
10. Emergency halt not active

## Rejection Logging

Every skip is logged with reason in bot live event stream.
