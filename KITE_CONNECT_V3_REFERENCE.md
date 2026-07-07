# Kite Connect v3 Reference (Workspace Guide)

Source: https://kite.trade/docs/connect/v3/
Last curated: 2026-07-02

## 1) Core Concepts

- Base REST URL: `https://api.kite.trade`
- WebSocket URL: `wss://ws.kite.trade?api_key=xxx&access_token=yyy`
- API version header: `X-Kite-Version: 3`
- Auth header format:
  - `Authorization: token <api_key>:<access_token>`
- Response envelope:
  - Success: `{ "status": "success", "data": ... }`
  - Error: `{ "status": "error", "message": "...", "error_type": "..." }`

Notes:
- GET/DELETE params => query string.
- POST/PUT params => form-encoded (`application/x-www-form-urlencoded`) unless endpoint explicitly requires JSON body (margins/charges endpoints).
- Timestamps are IST in format `yyyy-mm-dd hh:mm:ss`.

## 2) Authentication (Login Flow)

Flow summary:
1. Redirect user to:
   - `https://kite.zerodha.com/connect/login?v=3&api_key=<api_key>`
2. On success, redirect URL receives `request_token`.
3. Create checksum:
   - `sha256(api_key + request_token + api_secret)`
4. Exchange token:
   - `POST /session/token` with `api_key`, `request_token`, `checksum`
5. Receive `access_token` and use it in all further requests.

Important:
- Never expose `api_secret` in frontend/mobile app.
- `access_token` expires daily (typically 6 AM next day) unless invalidated earlier.

User endpoints:
- `POST /session/token`
- `GET /user/profile`
- `GET /user/margins`
- `GET /user/margins/:segment`
- `DELETE /session/token`

## 3) Error Handling and Rate Limits

Common HTTP codes:
- 400 bad input
- 403 token/session invalid
- 404 not found
- 405 method not allowed
- 410 gone
- 429 rate limit
- 500/502/503/504 server/backend issues

Exception types include:
- `TokenException`, `UserException`, `OrderException`, `InputException`, `MarginException`, `HoldingException`, `NetworkException`, `DataException`, `GeneralException`

Rate limits:
- Quote: 1 req/sec
- Historical: 3 req/sec
- Order placement: 10 req/sec
- All other endpoints: 10 req/sec

Trading safety limits:
- 400 orders/minute
- 10 orders/second
- 5000 orders/day per user/API key
- Max 25 modifications per order, then cancel/re-place

## 4) Orders API

Endpoints:
- `POST /orders/:variety`
- `PUT /orders/:variety/:order_id`
- `DELETE /orders/:variety/:order_id`
- `GET /orders`
- `GET /orders/:order_id`
- `GET /trades`
- `GET /orders/:order_id/trades`

Important constants:
- variety: `regular`, `amo`, `co`, `iceberg`, `auction`
- order_type: `MARKET`, `LIMIT`, `SL`, `SL-M`
- product: `CNC`, `NRML`, `MIS`, `MTF`
- validity: `DAY`, `IOC`, `TTL`

Advanced params:
- `market_protection`: `-1` auto or custom % `>0 <=100` (for MARKET/SL-M)
- `autoslice`: true/false (max 10 slices)
- `iceberg_legs`, `iceberg_quantity`
- `validity_ttl` for TTL orders
- `tag` alphanumeric max 20 chars

Order status lifecycle:
- Interim statuses like `PUT ORDER REQ RECEIVED`, `VALIDATION PENDING`, `OPEN PENDING`, `MODIFY PENDING`, `TRIGGER PENDING`, etc.
- Terminal/common statuses: `OPEN`, `COMPLETE`, `CANCELLED`, `REJECTED`

Best practice:
- Place order returns `order_id`, not final execution state.
- Use order history/postbacks/websocket order updates for true state tracking.

## 5) Portfolio API

Endpoints:
- `GET /portfolio/holdings`
- `GET /portfolio/positions`
- `PUT /portfolio/positions` (product conversion)
- `GET /portfolio/holdings/auctions`
- Holdings authorisation flow endpoint:
  - `POST /portfolio/holdings/authorise`

Key notes:
- Holdings: long-term demat equity.
- Positions: intraday and derivatives (`net` and `day` arrays).
- Exit by placing opposite-side order with same `product`.
- Holdings authorisation may throw HTTP 428 for sell if depository authorisation required.

## 6) Market Quotes and Instruments

Instrument dump:
- `GET /instruments`
- `GET /instruments/:exchange`
- Returns gzipped CSV, not JSON.
- Recommended caching once daily (around 08:30 AM).

Quote APIs (up to 250 instruments/call):
- `GET /quote`
- `GET /quote/ohlc`
- `GET /quote/ltp`

Instrument identity:
- `exchange:tradingsymbol` (example `NSE:INFY`)
- Response may omit missing/expired keys; always check key existence.

## 7) Historical Data API

Endpoint:
- `GET /instruments/historical/:instrument_token/:interval`

Intervals:
- `minute`, `day`, `3minute`, `5minute`, `10minute`, `15minute`, `30minute`, `60minute`

Query params:
- `from`, `to` (`yyyy-mm-dd hh:mm:ss`)
- `continuous=1` for continuous futures day candles (NFO/MCX futures)
- `oi=1` include open interest

Candles format:
- `[timestamp, open, high, low, close, volume]`
- with OI enabled, OI appears as additional field.

## 8) GTT API

Endpoints:
- `POST /gtt/triggers`
- `GET /gtt/triggers`
- `GET /gtt/triggers/:id`
- `PUT /gtt/triggers/:id`
- `DELETE /gtt/triggers/:id`

Types:
- `single` (1 trigger value)
- `two-leg` OCO (2 trigger values)

Payload components:
- `type`
- `condition` JSON
- `orders` JSON array

Trigger states:
- `active`, `triggered`, `disabled`, `expired`, `cancelled`, `rejected`, `deleted`

## 9) Margin and Charges APIs

Endpoints (JSON POST with `application/json`):
- `POST /margins/orders`
- `POST /margins/basket`
- `POST /charges/orders`

Notes:
- Basket margin supports `consider_positions=true`.
- `mode=compact` available for concise responses.
- Charges include tax breakdown (`transaction_tax`, exchange charges, SEBI, brokerage, stamp, GST).

## 10) Mutual Funds API

Endpoints:
- `GET /mf/orders`
- `GET /mf/orders/:order_id`
- `GET /mf/sips`
- `GET /mf/holdings`
- `GET /mf/instruments` (gzipped CSV)

Notes:
- MF APIs are Coin/STARMF specific.
- MF order placement from API is not provided as part of this section due to payment mandate flow.
- Dividend reinvestment schemes not supported (per docs note).

## 11) WebSocket Streaming

Connect:
- `wss://ws.kite.trade?api_key=xxx&access_token=yyy`

Actions (`a`, `v`):
- subscribe
- unsubscribe
- mode (`ltp`, `quote`, `full`)

Modes and packet sizes:
- `ltp`: 8 bytes
- `quote`: 44 bytes
- `full`: 184 bytes (includes market depth)

Limits:
- Up to 3000 instruments per connection
- Up to 3 websocket connections per API key

Important parsing notes:
- Market data => binary
- Order updates/errors/messages => text JSON
- 1-byte heartbeats can be ignored

## 12) Postbacks / Webhooks

- POSTed to configured `postback_url` on order status changes.
- Validate checksum:
  - `sha256(order_id + order_timestamp + api_secret)`
- Payload includes order fields similar to order book response.

Recommendation:
- For single-user apps, websocket order updates are usually simpler.
- For multi-user platform apps, postbacks are preferred.

## 13) Security Checklist

- Never commit `api_secret` and active `access_token` to source control.
- Keep secrets in environment vars or ignored config files.
- Rotate leaked keys/tokens immediately.
- Validate postback checksum for authenticity.
- Re-login on `TokenException` (403).

## 14) Implementation Checklist for This Workspace

- Keep instrument master cached locally and refresh daily.
- Use `quote/ohlc/ltp` in batches (up to 250 instruments).
- Use websocket for watchlists/live UI and avoid high-rate polling.
- Use postbacks or websocket order updates for order lifecycle.
- Implement retry with backoff for transient 5xx/network errors.
- Respect rate limits and trading limits.

## 15) Links

- Root docs: https://kite.trade/docs/connect/v3/
- User/auth: https://kite.trade/docs/connect/v3/user/
- Orders: https://kite.trade/docs/connect/v3/orders/
- Portfolio: https://kite.trade/docs/connect/v3/portfolio/
- Market/instruments: https://kite.trade/docs/connect/v3/market-quotes/
- Historical: https://kite.trade/docs/connect/v3/historical/
- GTT: https://kite.trade/docs/connect/v3/gtt/
- Margins: https://kite.trade/docs/connect/v3/margins/
- Mutual funds: https://kite.trade/docs/connect/v3/mutual-funds/
- WebSocket: https://kite.trade/docs/connect/v3/websocket/
- Postbacks: https://kite.trade/docs/connect/v3/postbacks/
- Errors: https://kite.trade/docs/connect/v3/exceptions/
- Response envelope: https://kite.trade/docs/connect/v3/response-structure/
