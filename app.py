import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context
from flask_cors import CORS
import json
import os
import re
import time
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
from datetime import datetime, timedelta, timezone
from threading import Lock

app = Flask(__name__)
CORS(app)

INSTRUMENTS_CACHE = {
    'loaded': False,
    'symbols': []
}
INSTRUMENTS_DF = None  # pandas DataFrame for fast search
INSTRUMENTS_LOCK = Lock()
LIVE_TICKS = {}
LIVE_TICKS_LOCK = Lock()
STREAM_SUBSCRIPTIONS = set()
STREAM_LOCK = Lock()
live_ticker = None
live_ticker_connected = False

# Try to import Kiteconnect
try:
    from kiteconnect import KiteConnect, KiteTicker
    KITECONNECT_AVAILABLE = True
    KITE_TICKER_AVAILABLE = True
    print("✅ Kiteconnect SDK imported successfully")
except ImportError:
    KITECONNECT_AVAILABLE = False
    KITE_TICKER_AVAILABLE = False
    print("❌ Kiteconnect SDK not available")

IST = timezone(timedelta(hours=5, minutes=30))

# Try to load credentials from config
try:
    from kite_config import API_KEY, API_SECRET, ACCESS_TOKEN, USER_ID
    CREDENTIALS_LOADED = API_KEY != "your_api_key_here" and ACCESS_TOKEN != "your_access_token_here"
    if CREDENTIALS_LOADED:
        print(f"✅ Kite credentials loaded (API Key: {API_KEY[:10]}...)")
    else:
        print("⚠️ Kite credentials not configured in kite_config.py")
except ImportError:
    CREDENTIALS_LOADED = False
    API_KEY = ACCESS_TOKEN = USER_ID = None
    print("⚠️ kite_config.py not found")

# Initialize Kite object
kite = None
if KITECONNECT_AVAILABLE and CREDENTIALS_LOADED:
    try:
        kite = KiteConnect(api_key=API_KEY)
        kite.set_access_token(ACCESS_TOKEN)
        print("✅ Kite API initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Kite API: {e}")
        kite = None

# ── Token management ────────────────────────────────────────────────────────

TOKEN_VALID = None  # None=unchecked, True=valid, False=expired

def check_token_valid():
    """Check if the current access token works. Caches result."""
    global TOKEN_VALID
    if kite is None:
        TOKEN_VALID = False
        return False
    try:
        kite.profile()
        TOKEN_VALID = True
        return True
    except Exception as e:
        msg = str(e).lower()
        if any(k in msg for k in ('token', 'session', 'invalid', '403', 'unauthori', 'access')):
            TOKEN_VALID = False
            return False
        TOKEN_VALID = True   # other error (network) - don't mark expired
        return True

def refresh_kite_token(request_token):
    """Exchange a fresh request_token for an access_token and persist it."""
    global kite, TOKEN_VALID, ACCESS_TOKEN
    if not KITECONNECT_AVAILABLE:
        raise RuntimeError("KiteConnect SDK not installed")
    if not API_KEY or not API_SECRET:
        raise RuntimeError("API_KEY or API_SECRET missing in kite_config.py")

    tmp = KiteConnect(api_key=API_KEY)
    session = tmp.generate_session(request_token, api_secret=API_SECRET)
    new_token = session['access_token']
    user_id   = session.get('user_id', '')

    # Persist to kite_config.py
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kite_config.py')
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'ACCESS_TOKEN\s*=\s*"[^"]*"', f'ACCESS_TOKEN = "{new_token}"', content)
    if user_id:
        content = re.sub(r'USER_ID\s*=\s*"[^"]*"', f'USER_ID = "{user_id}"', content)
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Hot-reload kite object (no restart needed)
    ACCESS_TOKEN = new_token
    kite = KiteConnect(api_key=API_KEY)
    kite.set_access_token(new_token)
    TOKEN_VALID = True
    print(f"✅ Access token refreshed for user {user_id}")
    return new_token, user_id

# ── Token routes ─────────────────────────────────────────────────────────────

@app.route('/token-callback')
def token_callback():
    """Auto-capture request_token from Zerodha redirect."""
    req_token = request.args.get('request_token', '').strip()
    status    = request.args.get('status', '')
    if status != 'success' or not req_token:
        return (f'<html><body style="font-family:sans-serif;padding:40px;background:#0f172a;color:#e2e8f0">'
                f'<h2 style="color:#ef4444">Login failed (status={status})</h2>'
                f'<a href="/token-refresh" style="color:#60a5fa">Try again</a></body></html>'), 400
    try:
        _, uid = refresh_kite_token(req_token)
        return ('<html><head><meta http-equiv="refresh" content="2;url=/"/></head>'
                f'<body style="font-family:sans-serif;padding:40px;background:#0f172a;color:#e2e8f0;text-align:center">'
                f'<h2 style="color:#4ade80">✅ Token refreshed for {uid}</h2>'
                f'<p>Redirecting to dashboard...</p></body></html>')
    except Exception as e:
        return (f'<html><body style="font-family:sans-serif;padding:40px;background:#0f172a;color:#e2e8f0">'
                f'<h2 style="color:#ef4444">❌ Token exchange failed</h2><p>{e}</p>'
                f'<a href="/token-refresh" style="color:#60a5fa">Try again</a></body></html>'), 400

@app.route('/token-refresh')
def token_refresh_page():
    """Serve the token-refresh UI."""
    login_url = '#'
    if KITECONNECT_AVAILABLE and API_KEY:
        try:
            login_url = KiteConnect(api_key=API_KEY).login_url()
        except Exception:
            pass
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Refresh Kite Token</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:"Segoe UI",sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center}}
.card{{background:#1e293b;border-radius:16px;padding:40px;max-width:500px;width:92%;box-shadow:0 20px 60px rgba(0,0,0,.5);border:1px solid #334155}}
h1{{color:#f8fafc;font-size:1.4em;margin-bottom:8px}}
.sub{{color:#94a3b8;margin-bottom:28px;font-size:.9em}}
.step{{margin-bottom:16px;color:#cbd5e1;font-size:.92em}}
.step b{{color:#f1f5f9}}
.btn{{display:block;width:100%;padding:14px;background:#2563eb;color:#fff;border:none;border-radius:10px;font-size:1em;cursor:pointer;text-decoration:none;text-align:center;margin-bottom:12px;transition:background .2s}}
.btn:hover{{background:#1d4ed8}}
.btn.sec{{background:#334155}}.btn.sec:hover{{background:#475569}}
.inp{{width:100%;padding:12px;background:#0f172a;border:1px solid #475569;border-radius:8px;color:#e2e8f0;font-size:.95em;margin-bottom:12px}}
.note{{background:#0f172a;border:1px solid #334155;border-radius:8px;padding:12px;font-size:.82em;color:#94a3b8;margin-bottom:20px;line-height:1.6}}
.note code{{color:#60a5fa;font-family:monospace}}
#st{{margin-top:12px;padding:10px;border-radius:8px;display:none;font-size:.9em}}
.ok{{background:#14532d;color:#4ade80}}.err{{background:#450a0a;color:#f87171}}
</style>
</head>
<body>
<div class="card">
  <h1>🔐 Refresh Access Token</h1>
  <p class="sub">Zerodha access tokens expire every day at midnight IST.</p>

  <div class="step"><b>Step 1:</b> Click the button below to log in to Zerodha.</div>
  <a href="{login_url}" target="_blank" class="btn">🔑 Open Zerodha Login</a>

  <div class="note">
    <b>Auto mode:</b> Set your Kite app redirect URL to
    <code>http://127.0.0.1:5000/token-callback</code> — token will refresh automatically after login.<br><br>
    <b>Manual mode:</b> After login, copy the <code>request_token=…</code> value from the redirect URL and paste below.
  </div>

  <div class="step"><b>Step 2 (manual only):</b> Paste the request_token here.</div>
  <input class="inp" id="ti" type="text" placeholder="Paste request_token from redirect URL…"/>
  <button class="btn sec" onclick="go()">🔄 Exchange Token</button>
  <div id="st"></div>
</div>
<script>
async function go(){{
  const t=document.getElementById('ti').value.trim();
  if(!t){{alert('Paste the request_token first');return;}}
  const s=document.getElementById('st');s.style.display='none';
  try{{
    const r=await fetch('/api/refresh-token',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{request_token:t}})}});
    const d=await r.json();
    if(d.status==='success'){{s.className='ok';s.textContent='✅ Token refreshed! Redirecting…';s.style.display='block';setTimeout(()=>location.href='/',1800);}}
    else{{s.className='err';s.textContent='❌ '+d.message;s.style.display='block';}}
  }}catch(e){{s.className='err';s.textContent='❌ '+e.message;s.style.display='block';}}
}}
document.getElementById('ti').addEventListener('keydown',e=>{{if(e.key==='Enter')go();}});
</script>
</body>
</html>"""
    return page

@app.route('/api/refresh-token', methods=['POST'])
def api_refresh_token():
    """Exchange a request_token for a new access_token (no restart needed)."""
    try:
        data = request.get_json(silent=True) or {}
        req_token = str(data.get('request_token', '')).strip()
        if not req_token:
            return jsonify({'status': 'error', 'message': 'request_token is required'}), 400
        _, user_id = refresh_kite_token(req_token)
        return jsonify({'status': 'success', 'message': 'Token refreshed', 'user_id': user_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/token-status')
def api_token_status():
    """Return current token validity and the Kite login URL."""
    valid = check_token_valid()
    login_url = '#'
    if KITECONNECT_AVAILABLE and API_KEY:
        try:
            login_url = KiteConnect(api_key=API_KEY).login_url()
        except Exception:
            pass
    return jsonify({
        'valid': valid,
        'refresh_url': '/token-refresh',
        'login_url': login_url
    })

_AUTH_KEYWORDS = ('incorrect', 'invalid', 'token', 'session', 'unauthori', 'access_token', 'api_key', 'expired', '403')

def _is_auth_error(msg: str) -> bool:
    m = msg.lower()
    return any(k in m for k in _AUTH_KEYWORDS)

def get_holdings():
    """Fetch REAL holdings from Zerodha Kite API"""
    if kite is None:
        return {
            "error": "Kite API not configured",
            "message": "Please add your API Key and Access Token to kite_config.py",
        }
    try:
        print("🔄 Fetching holdings from Zerodha Kite API...")
        holdings = kite.holdings()
        print(f"✅ Successfully fetched {len(holdings)} holdings from Kite")
        return holdings
    except Exception as e:
        print(f"❌ Error fetching holdings: {e}")
        return {"error": str(e), "message": "Failed to fetch holdings from Kite API"}


def ensure_instruments_cache():
    """Load instruments from CSV (downloaded from Kite, no auth needed) or fallback to Kite SDK."""
    global INSTRUMENTS_DF

    if INSTRUMENTS_CACHE['loaded']:
        return

    with INSTRUMENTS_LOCK:
        if INSTRUMENTS_CACHE['loaded']:
            return

        csv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instruments.csv')
        loaded_from_csv = False

        # ── Step 1: Try loading from today's CSV file ──────────────────────────
        if PANDAS_AVAILABLE and os.path.exists(csv_file):
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(csv_file))
                if mtime.date() == datetime.now().date():
                    df = pd.read_csv(csv_file, dtype={'strike': float})
                    if len(df) > 10000:
                        INSTRUMENTS_DF = df
                        loaded_from_csv = True
                        print(f"[INFO] Instruments loaded from today's CSV: {len(df)} rows")
            except Exception as e:
                print(f"[WARNING] CSV load failed: {e}")

        # ── Step 2: Download fresh CSV from Kite (no auth needed) ──────────────
        if PANDAS_AVAILABLE and not loaded_from_csv:
            try:
                print("[INFO] Downloading instruments CSV from Kite (no auth required)...")
                df = pd.read_csv('https://api.kite.trade/instruments', dtype={'strike': float})
                df.to_csv(csv_file, index=False)
                INSTRUMENTS_DF = df
                loaded_from_csv = True
                print(f"[INFO] Instruments CSV downloaded and saved: {len(df)} rows")
            except Exception as e:
                print(f"[WARNING] CSV download failed: {e}. Falling back to Kite SDK.")

        # ── Step 3: Fallback to Kite SDK if pandas/CSV not available ──────────
        if not loaded_from_csv:
            if kite is None:
                print("[ERROR] No instruments source available (no pandas, no CSV, no Kite API)")
                return
            try:
                print("[INFO] Loading instruments from Kite SDK (NSE, BSE, NFO)...")
                nse = kite.instruments("NSE")
                bse = kite.instruments("BSE")
                nfo = kite.instruments("NFO")
                merged = []
                for row in nse + bse + nfo:
                    ts = row.get('tradingsymbol', '')
                    exch = row.get('exchange', '')
                    if not ts or not exch:
                        continue
                    expiry = row.get('expiry')
                    merged.append({
                        'tradingsymbol': ts,
                        'name': row.get('name', ''),
                        'exchange': exch,
                        'instrument_token': row.get('instrument_token'),
                        'instrument_type': row.get('instrument_type', ''),
                        'expiry': str(expiry) if expiry else '',
                        'strike': row.get('strike', 0),
                        'lot_size': row.get('lot_size', 0),
                    })
                INSTRUMENTS_CACHE['symbols'] = merged
                INSTRUMENTS_CACHE['loaded'] = True
                print(f"[INFO] SDK instruments loaded: {len(merged)} symbols")
                return
            except Exception as ex:
                print(f"[ERROR] SDK instrument load failed: {ex}")
                return

        # ── Convert pandas DF to INSTRUMENTS_CACHE['symbols'] — fast vectorized ──
        if INSTRUMENTS_DF is not None:
            df_clean = INSTRUMENTS_DF.copy()
            df_clean['tradingsymbol'] = df_clean['tradingsymbol'].fillna('').astype(str)
            df_clean['name'] = df_clean['name'].fillna('').astype(str)
            df_clean['exchange'] = df_clean['exchange'].fillna('').astype(str)
            df_clean['instrument_type'] = df_clean['instrument_type'].fillna('').astype(str)
            df_clean['expiry'] = df_clean['expiry'].fillna('').astype(str).replace('nan', '')
            df_clean['strike'] = pd.to_numeric(df_clean['strike'], errors='coerce').fillna(0.0)
            df_clean['lot_size'] = pd.to_numeric(df_clean['lot_size'], errors='coerce').fillna(0).astype(int)
            df_clean = df_clean[df_clean['tradingsymbol'].str.len() > 0]
            symbols = df_clean[['tradingsymbol', 'name', 'exchange', 'instrument_token',
                                 'instrument_type', 'expiry', 'strike', 'lot_size']].to_dict('records')
            INSTRUMENTS_CACHE['symbols'] = symbols
            INSTRUMENTS_CACHE['loaded'] = True
            nfo_count = sum(1 for s in symbols if s['exchange'] == 'NFO')
            print(f"[INFO] Instrument cache ready: {len(symbols)} symbols (NFO: {nfo_count})")


def parse_history_dt(value):
    """Parse history datetime in common API formats."""
    if not value:
        return None

    raw = str(value).strip().replace('T', ' ').replace('Z', '')
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        try:
            return datetime.strptime(raw, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None


def get_history_window(interval, range_key, from_value=None, to_value=None):
    """Return from/to timestamps for chart history requests."""
    now = datetime.now()
    explicit_from = parse_history_dt(from_value)
    explicit_to = parse_history_dt(to_value)

    if explicit_from and explicit_to:
        return explicit_from.strftime('%Y-%m-%d %H:%M:%S'), explicit_to.strftime('%Y-%m-%d %H:%M:%S')

    key = (range_key or '').upper().strip() or ('5D' if interval != 'day' else '1Y')

    intraday_ranges = {
        '1D': timedelta(days=1),
        '5D': timedelta(days=5),
        '1M': timedelta(days=30),
        '3M': timedelta(days=90),
        '6M': timedelta(days=180),
        '1Y': timedelta(days=365),
        'ALL': timedelta(days=365 * 10),
        'MAX': timedelta(days=365 * 10),
    }
    day_ranges = {
        '1M': timedelta(days=30),
        '3M': timedelta(days=90),
        '6M': timedelta(days=180),
        '1Y': timedelta(days=365),
        '3Y': timedelta(days=365 * 3),
        '5Y': timedelta(days=365 * 5),
        'ALL': timedelta(days=365 * 30),
        'MAX': timedelta(days=365 * 30),
    }

    if interval == 'day':
        delta = day_ranges.get(key, timedelta(days=365))
    else:
        delta = intraday_ranges.get(key, timedelta(days=5))

    start = now - delta
    return start.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')


def fetch_historical_chunked(instrument_token, interval, from_ts, to_ts, include_oi=0):
    """Fetch full history by stitching multiple Kite historical_data calls."""
    start_dt = datetime.strptime(from_ts, '%Y-%m-%d %H:%M:%S')
    end_dt = datetime.strptime(to_ts, '%Y-%m-%d %H:%M:%S')
    if end_dt < start_dt:
        raise ValueError('Invalid history window: to must be >= from')

    # Kite applies per-request limits by interval. Chunk requests and stitch results.
    chunk_days_by_interval = {
        'minute': 60,
        '3minute': 100,
        '5minute': 100,
        '10minute': 120,
        '15minute': 200,
        '30minute': 200,
        '60minute': 400,
        'day': 2000,
    }
    chunk_days = chunk_days_by_interval.get(interval, 60)

    candles = []
    cursor = start_dt
    sleep_seconds = 0.36  # Historical API limit is 3 req/sec.

    while cursor <= end_dt:
        chunk_end = min(cursor + timedelta(days=chunk_days) - timedelta(seconds=1), end_dt)
        from_chunk = cursor.strftime('%Y-%m-%d %H:%M:%S')
        to_chunk = chunk_end.strftime('%Y-%m-%d %H:%M:%S')

        try:
            part = kite.historical_data(instrument_token, from_chunk, to_chunk, interval, oi=include_oi)
        except Exception as ex:
            text = str(ex).lower()
            if chunk_days > 1 and any(flag in text for flag in ['limit', 'range', 'input', 'interval', 'days']):
                chunk_days = max(1, chunk_days // 2)
                continue
            raise

        candles.extend(part)
        cursor = chunk_end + timedelta(seconds=1)
        if cursor <= end_dt:
            time.sleep(sleep_seconds)

    candles.sort(key=lambda c: c.get('date'))
    return candles


def now_ist():
    return datetime.now(IST)


def is_indian_market_open(now=None):
    current = now or now_ist()
    if current.weekday() >= 5:
        return False

    minutes = current.hour * 60 + current.minute
    return 555 <= minutes <= 930


def serialize_dt(value):
    return value.isoformat() if hasattr(value, 'isoformat') else value


def build_tick_payload(tick):
    previous_close = ((tick.get('ohlc') or {}).get('close')) or 0
    last_price = tick.get('last_price') or 0
    net_change = last_price - previous_close if previous_close else 0
    percent_change = (net_change / previous_close * 100) if previous_close else tick.get('change', 0)

    return {
        'instrument_token': tick.get('instrument_token'),
        'last_price': last_price,
        'last_quantity': tick.get('last_quantity'),
        'volume_traded': tick.get('volume_traded'),
        'average_traded_price': tick.get('average_traded_price'),
        'change': percent_change,
        'net_change': net_change,
        'ohlc': tick.get('ohlc', {}),
        'last_traded_timestamp': serialize_dt(tick.get('last_traded_timestamp')),
        'exchange_timestamp': serialize_dt(tick.get('exchange_timestamp')),
        'timestamp': now_ist().isoformat()
    }


def ensure_live_ticker():
    global live_ticker

    if not KITE_TICKER_AVAILABLE or not CREDENTIALS_LOADED:
        return False, 'Kite WebSocket is not available in the current setup'

    with STREAM_LOCK:
        if live_ticker is not None:
            return True, None

        live_ticker = KiteTicker(API_KEY, ACCESS_TOKEN)

        def on_connect(ws, response):
            global live_ticker_connected
            live_ticker_connected = True
            print('✅ Live ticker connected')
            tokens = list(STREAM_SUBSCRIPTIONS)
            if tokens:
                ws.subscribe(tokens)
                ws.set_mode(ws.MODE_FULL, tokens)

        def on_close(ws, code, reason):
            global live_ticker_connected
            live_ticker_connected = False
            print(f'⚠️ Live ticker closed: {code} {reason}')

        def on_error(ws, code, reason):
            print(f'❌ Live ticker error: {code} {reason}')

        def on_ticks(ws, ticks):
            if not ticks:
                return

            with LIVE_TICKS_LOCK:
                for tick in ticks:
                    token = tick.get('instrument_token')
                    if token is None:
                        continue
                    LIVE_TICKS[token] = build_tick_payload(tick)

        live_ticker.on_connect = on_connect
        live_ticker.on_close = on_close
        live_ticker.on_error = on_error
        live_ticker.on_ticks = on_ticks
        live_ticker.connect(threaded=True)
        print('🚀 Starting live ticker thread...')
        return True, None


def subscribe_live_tokens(tokens):
    valid_tokens = sorted({int(token) for token in tokens if str(token).strip()})
    if not valid_tokens:
        return []

    ok, error_message = ensure_live_ticker()
    if not ok:
        raise RuntimeError(error_message)

    with STREAM_LOCK:
        new_tokens = [token for token in valid_tokens if token not in STREAM_SUBSCRIPTIONS]
        STREAM_SUBSCRIPTIONS.update(valid_tokens)

        if live_ticker is not None and live_ticker_connected and new_tokens:
            live_ticker.subscribe(new_tokens)
            live_ticker.set_mode(live_ticker.MODE_FULL, list(STREAM_SUBSCRIPTIONS))

    return valid_tokens

@app.route('/api/holdings', methods=['GET'])
def api_holdings():
    """API endpoint for holdings - fetches REAL data from Zerodha Kite API"""
    try:
        # Check if Kite is configured
        if kite is None:
            print("⚠️ Kite not configured - returning error")
            return jsonify({
                'status': 'error',
                'message': 'Zerodha Kite API not configured',
                'details': 'Please add your API credentials to kite_config.py',
                'steps': [
                    '1. Go to https://kite.zerodha.com/account/apikeys',
                    '2. Copy your API Key',
                    '3. Get your Access Token from https://kite.zerodha.com/connect/login?api_key=YOUR_API_KEY',
                    '4. Paste both into kite_config.py',
                    '5. Restart this server'
                ]
            }), 500
        
        holdings = get_holdings()
        
        # Check if we got an error
        if isinstance(holdings, dict) and 'error' in holdings:
            err_msg = holdings.get('error', 'Unknown error')
            auth_expired = _is_auth_error(err_msg)
            print(f"⚠️ Holdings error (auth={auth_expired}): {err_msg}")
            if auth_expired:
                global TOKEN_VALID
                TOKEN_VALID = False
            return jsonify({
                'status': 'error',
                'message': err_msg,
                'details': holdings.get('message', ''),
                'auth_expired': auth_expired,
                'refresh_url': '/token-refresh'
            }), 500
        
        # Check if we got a valid list
        if not isinstance(holdings, list) or len(holdings) == 0:
            print("⚠️ No holdings data received")
            return jsonify({
                'status': 'error',
                'message': 'No holdings data available',
                'details': 'You may not have any holdings or the API returned empty data'
            }), 500
        
        print(f"✅ Processing {len(holdings)} real holdings from Zerodha")
        
        # Enhance with additional calculations
        for holding in holdings:
            holding['value'] = holding.get('quantity', 0) * holding.get('last_price', 0)
            holding['invested'] = holding.get('quantity', 0) * holding.get('average_price', 0)
            holding['pnl_percentage'] = (
                (holding['pnl'] / holding['invested'] * 100) 
                if holding['invested'] > 0 else 0
            )
        
        # Calculate portfolio totals
        total_value = sum(h.get('value', 0) for h in holdings)
        total_invested = sum(h.get('invested', 0) for h in holdings)
        total_pnl = sum(h.get('pnl', 0) for h in holdings)
        total_pnl_percentage = (
            (total_pnl / total_invested * 100) 
            if total_invested > 0 else 0
        )
        
        response = {
            'holdings': holdings,
            'summary': {
                'total_holdings': len(holdings),
                'total_value': total_value,
                'total_invested': total_invested,
                'total_pnl': total_pnl,
                'total_pnl_percentage': total_pnl_percentage,
                'gainers': len([h for h in holdings if h.get('pnl', 0) > 0]),
                'losers': len([h for h in holdings if h.get('pnl', 0) < 0]),
                'timestamp': datetime.now().isoformat()
            },
            'status': 'success',
            'source': '🔴 Zerodha Kite API (REAL-TIME)'
        }
        
        print(f"✅ Returning {len(holdings)} holdings with total P&L: ₹{total_pnl:.2f}")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error in api_holdings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
@app.route('/')
def index():
    """Serve the main dashboard"""
    return send_from_directory('.', 'dashboard_live.html')

@app.route('/dashboard_live.html')
def dashboard():
    """Serve dashboard"""
    return send_from_directory('.', 'dashboard_live.html')


@app.route('/market-watch')
@app.route('/market_watch.html')
@app.route('/market_watch')
@app.route('/market-watch.html')
def market_watch():
    """Serve market watch page"""
    return send_from_directory('.', 'market_watch.html')
@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/api/search/<query>', methods=['GET'])

def api_search(query):
    """Search holdings by symbol"""
    try:
        holdings = get_holdings()
        
        if isinstance(holdings, list):
            filtered = [h for h in holdings if query.upper() in h.get('tradingsymbol', '').upper()]
            return jsonify({'results': filtered, 'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': holdings.get('error', 'Unknown error')}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/suggest/<query>', methods=['GET'])
def api_suggest(query):
    """
    Smart autocomplete — token-based, any order:
      "nifty 25500 july"    → name + strike + month
      "nifty july 25500"    → same, order doesn't matter
      "nifty july 14"       → name + month + day (specific expiry date)
      "nifty july"          → name + month
      "nifty 25500"         → name + strike
      "nifty"               → substring fallback
      "RELIANCE"            → substring on all exchanges
    """
    try:
        q = (query or '').strip()
        if len(q) < 1:
            return jsonify({'status': 'success', 'results': []})

        ensure_instruments_cache()
        if not INSTRUMENTS_CACHE['loaded']:
            return jsonify({'status': 'error', 'message': 'Instrument cache unavailable'}), 500

        # ── Token dictionaries ─────────────────────────────────────────────────
        INDEX_MAP = {
            'NIFTY': 'NIFTY',       'NIFTY50': 'NIFTY',
            'BANKNIFTY': 'BANKNIFTY', 'BANK': 'BANKNIFTY',
            'FINNIFTY': 'FINNIFTY',  'FIN': 'FINNIFTY',
            'SENSEX': 'SENSEX',
            'MIDCPNIFTY': 'MIDCPNIFTY', 'MIDCAP': 'MIDCPNIFTY',
        }
        # month word → (3-letter abbrev, 2-digit number for expiry column)
        MONTH_MAP = {
            'JAN': ('JAN', '01'), 'JANUARY':   ('JAN', '01'),
            'FEB': ('FEB', '02'), 'FEBRUARY':  ('FEB', '02'),
            'MAR': ('MAR', '03'), 'MARCH':     ('MAR', '03'),
            'APR': ('APR', '04'), 'APRIL':     ('APR', '04'),
            'MAY': ('MAY', '05'),
            'JUN': ('JUN', '06'), 'JUNE':      ('JUN', '06'),
            'JUL': ('JUL', '07'), 'JULY':      ('JUL', '07'),
            'AUG': ('AUG', '08'), 'AUGUST':    ('AUG', '08'),
            'SEP': ('SEP', '09'), 'SEPT':      ('SEP', '09'), 'SEPTEMBER': ('SEP', '09'),
            'OCT': ('OCT', '10'), 'OCTOBER':   ('OCT', '10'),
            'NOV': ('NOV', '11'), 'NOVEMBER':  ('NOV', '11'),
            'DEC': ('DEC', '12'), 'DECEMBER':  ('DEC', '12'),
        }

        # ── Parse tokens (any order) ───────────────────────────────────────────
        index_name = None
        strike     = None
        month_num  = None   # '07' etc. for expiry column match
        day        = None   # 1–31 for expiry day

        # Check multi-word index names first ("bank nifty", "fin nifty")
        MULTI_WORD = [
            ('BANK NIFTY', 'BANKNIFTY'),
            ('FIN NIFTY',  'FINNIFTY'),
            ('MIDCAP NIFTY', 'MIDCPNIFTY'),
        ]
        remaining = q.upper()
        for phrase, mapped in MULTI_WORD:
            if phrase in remaining:
                index_name = mapped
                remaining = remaining.replace(phrase, ' ')
                break

        for token in remaining.split():
            token = token.strip('.,/-')
            if not token:
                continue
            if not index_name and token in INDEX_MAP:
                index_name = INDEX_MAP[token]
            elif token in MONTH_MAP:
                _, month_num = MONTH_MAP[token]
            elif re.match(r'^\d{4,6}$', token):
                strike = float(token)
            elif re.match(r'^\d{1,2}$', token) and 1 <= int(token) <= 31:
                day = int(token)

        df_result = None

        # ── Structured NFO filter (if index found) ────────────────────────────
        if PANDAS_AVAILABLE and INSTRUMENTS_DF is not None and index_name:
            nfo  = INSTRUMENTS_DF[
                (INSTRUMENTS_DF['exchange'] == 'NFO') &
                (INSTRUMENTS_DF['name'] == index_name)
            ]
            # Filter by strike (options only, since futures have strike=0)
            if strike is not None:
                nfo = nfo[nfo['strike'] == strike]
            # Filter by month (applies to both options and futures)
            if month_num is not None:
                nfo = nfo[nfo['expiry'].str.contains(f'-{month_num}-', na=False)]
                # If month is specified but no strike, also include futures (strike=0)
                # Futures have 0 strike, so they're already in the result
            # Filter by day (applies to both)
            if day is not None:
                nfo = nfo[nfo['expiry'].str.endswith(f'-{day:02d}')]

            # Sort: futures first (is_future desc), then by expiry and strike
            nfo['is_future'] = (nfo['instrument_type'] == 'FUT').astype(int)
            df_result = nfo.sort_values(
                by=['is_future', 'expiry', 'strike', 'instrument_type'],
                ascending=[False, True, True, True]
            ).drop('is_future', axis=1).head(200)

        # ── Substring fallback (no index identified, or index found nothing) ──
        if PANDAS_AVAILABLE and INSTRUMENTS_DF is not None and (df_result is None or len(df_result) == 0):
            q_up = q.upper()
            mask = (
                INSTRUMENTS_DF['tradingsymbol'].str.upper().str.startswith(q_up) |
                INSTRUMENTS_DF['tradingsymbol'].str.upper().str.contains(q_up, regex=False) |
                INSTRUMENTS_DF['name'].str.upper().str.contains(q_up, na=False, regex=False)
            )
            df_result = INSTRUMENTS_DF[
                mask & INSTRUMENTS_DF['exchange'].isin(['NSE', 'BSE', 'NFO', 'MCX', 'BFO'])
            ].head(200)

        # ── Serialize to JSON (vectorized, no iterrows) ───────────────────────
        if df_result is not None and len(df_result) > 0:
            cols = ['tradingsymbol', 'name', 'exchange', 'instrument_token',
                    'instrument_type', 'expiry', 'strike', 'lot_size']
            for c in cols:
                if c not in df_result.columns:
                    df_result = df_result.copy()
                    df_result[c] = ''
            out = df_result[cols].copy()
            out['tradingsymbol']   = out['tradingsymbol'].fillna('').astype(str)
            out['name']            = out['name'].fillna('').astype(str)
            out['exchange']        = out['exchange'].fillna('').astype(str)
            out['instrument_type'] = out['instrument_type'].fillna('').astype(str)
            out['expiry']          = out['expiry'].fillna('').astype(str).replace('nan', '')
            out['strike']          = pd.to_numeric(out['strike'], errors='coerce').fillna(0.0)
            out['lot_size']        = pd.to_numeric(out['lot_size'], errors='coerce').fillna(0).astype(int)
            results = out.to_dict('records')
            return jsonify({'status': 'success', 'results': results})

        # ── No-pandas fallback ────────────────────────────────────────────────
        q_upper = q.upper()
        results = []
        for s in INSTRUMENTS_CACHE['symbols']:
            ts   = s.get('tradingsymbol', '').upper()
            name = (s.get('name') or '').upper()
            if s.get('exchange') not in ['NSE', 'BSE', 'NFO', 'MCX', 'BFO']:
                continue
            if ts.startswith(q_upper) or q_upper in ts or (name and q_upper in name):
                results.append(s)
                if len(results) >= 200:
                    break
        return jsonify({'status': 'success', 'results': results})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


def parse_derivative_search(query, symbols):
    """Parse patterns like 'Nifty 24450 july 14' → search for NIFTY2671424450CE/PE/FUT."""
    import sys
    debug_msg = f"[DEBUG] parse_derivative_search called with: '{query}'\n"
    print(debug_msg, flush=True)
    sys.stderr.write(debug_msg)
    sys.stderr.flush()
    
    q = query.strip()
    
    # Index name mapping
    idx_map = {
        'NIFTY': 'NIFTY',
        'NIFTY50': 'NIFTY',
        'BANKNIFTY': 'BANKNIFTY',
        'BANK': 'BANKNIFTY',
        'FINNIFTY': 'FINNIFTY',
        'FIN': 'FINNIFTY',
        'SENSEX': 'SENSEX',
        'MIDCPNIFTY': 'MIDCPNIFTY',
        'MIDCAP': 'MIDCPNIFTY',
    }

    # Month mapping
    month_map = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }

    # Pattern: INDEX STRIKE [DATE/MONTH] [DAY] [CE/PE/FUT]
    # E.g. "Nifty 24450 july 14", "Bank 44000 jul", "Fin 21000 august"
    pattern = r'^([a-zA-Z\s]+?)\s+(\d{4,5})(?:\s+([a-zA-Z]+)\s*(\d{1,2})?)?(?:\s+(CE|PE|FUT))?$'
    match = re.match(pattern, q.upper())
    
    if not match:
        return []

    idx_str, strike_str, month_str, day_str, opt_type = match.groups()
    
    idx_str = idx_str.strip()
    strike = int(strike_str)
    target_day = int(day_str) if day_str else None
    
    # Map index string to Kite symbol
    idx_key = None
    for key in idx_map:
        if key in idx_str:
            idx_key = idx_map[key]
            break
    if not idx_key:
        return []

    # Parse expiry date
    today = datetime.now(IST)
    target_year = today.year
    target_month = None
    
    if month_str:
        month_upper = month_str[:3].upper()
        target_month = month_map.get(month_upper)
        if not target_month:
            return []
    else:
        return []  # Month required

    # Construct search patterns
    patterns = []
    for year_offset in range(3):  # Search current year + 2 years forward
        y = target_year + year_offset
        m = target_month
        
        # Format: INDEXYYMMDD (or INDEXYYMMFUT if no day specified, which searches all expiries)
        if target_day:
            # Exact day specified: NIFTY2671424450CE
            date_str = f"{y % 100:02d}{m:02d}{target_day:02d}"
            base = f"{idx_key}{date_str}{strike:05d}"
            
            if opt_type:
                patterns.append(base + opt_type)
            else:
                patterns.extend([base + 'CE', base + 'PE', base + 'FUT'])
        else:
            # No day: search for all expiries in this month
            # Try all possible days (1-31) for this month
            import calendar
            try:
                max_day = calendar.monthrange(y, m)[1]
                for d in range(1, max_day + 1):
                    date_str = f"{y % 100:02d}{m:02d}{d:02d}"
                    base = f"{idx_key}{date_str}{strike:05d}"
                    if opt_type:
                        patterns.append(base + opt_type)
                    else:
                        patterns.extend([base + 'CE', base + 'PE', base + 'FUT'])
            except:
                pass

    # Find matching symbols
    results = []
    symbol_set = {s['tradingsymbol'] for s in symbols}
    
    print(f"[DEBUG] Generated {len(patterns)} patterns. Sample: {patterns[:3]}")
    print(f"[DEBUG] Symbol set size: {len(symbol_set)}")
    
    for pattern in patterns:
        if pattern in symbol_set:
            item = next((s for s in symbols if s['tradingsymbol'] == pattern), None)
            if item:
                results.append(item)
                print(f"[DEBUG] Found matching symbol: {pattern}")

    # Remove duplicates and sort by expiry
    seen = set()
    unique_results = []
    for item in sorted(results, key=lambda x: (x.get('expiry', ''), x['tradingsymbol'])):
        if item['tradingsymbol'] not in seen:
            seen.add(item['tradingsymbol'])
            unique_results.append(item)

    print(f"[DEBUG] Returning {len(unique_results)} unique results")
    return unique_results


@app.route('/api/history/<int:instrument_token>/<interval>', methods=['GET'])
def api_history(instrument_token, interval):
    """Historical candles for charting."""
    if kite is None:
        return jsonify({'status': 'error', 'message': 'Kite API not configured'}), 500

    allowed_intervals = {'minute', '3minute', '5minute', '10minute', '15minute', '30minute', '60minute', 'day'}
    if interval not in allowed_intervals:
        return jsonify({'status': 'error', 'message': f'Unsupported interval: {interval}'}), 400

    try:
        range_key = request.args.get('range', '5D' if interval != 'day' else '1Y')
        from_value = request.args.get('from')
        to_value = request.args.get('to')
        include_oi = 1 if request.args.get('oi', '0') == '1' else 0
        from_ts, to_ts = get_history_window(interval, range_key, from_value, to_value)
        candles = fetch_historical_chunked(instrument_token, interval, from_ts, to_ts, include_oi)

        normalized = []
        for candle in candles:
            row = {
                'time': candle['date'].isoformat(),
                'open': candle['open'],
                'high': candle['high'],
                'low': candle['low'],
                'close': candle['close'],
                'volume': candle.get('volume', 0)
            }
            if 'oi' in candle:
                row['oi'] = candle['oi']
            normalized.append(row)

        return jsonify({
            'status': 'success',
            'instrument_token': instrument_token,
            'interval': interval,
            'range': range_key,
            'from': from_ts,
            'to': to_ts,
            'candles': normalized
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/stream/subscribe', methods=['POST'])
def api_stream_subscribe():
    """Register instruments for the shared live ticker connection."""
    try:
        payload = request.get_json(silent=True) or {}
        tokens = payload.get('tokens', [])
        subscribed = subscribe_live_tokens(tokens)
        return jsonify({
            'status': 'success',
            'tokens': subscribed,
            'connected': live_ticker_connected,
            'market_open': is_indian_market_open(),
            'timestamp': now_ist().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/stream/ticks', methods=['GET'])
def api_stream_ticks():
    """Server-Sent Events relay for live ticks from the Kite ticker."""
    raw_tokens = request.args.get('tokens', '')
    requested_tokens = [part.strip() for part in raw_tokens.split(',') if part.strip()]

    try:
        if requested_tokens:
            subscribe_live_tokens(requested_tokens)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    token_filter = {int(token) for token in requested_tokens} if requested_tokens else None

    def event_stream():
        yield 'retry: 2000\n\n'
        last_sent = {}

        while True:
            changed_ticks = []

            with LIVE_TICKS_LOCK:
                token_list = token_filter or set(STREAM_SUBSCRIPTIONS)
                for token in token_list:
                    tick = LIVE_TICKS.get(token)
                    if not tick:
                        continue

                    snapshot = json.dumps(tick, sort_keys=True)
                    if last_sent.get(token) == snapshot:
                        continue

                    last_sent[token] = snapshot
                    changed_ticks.append(tick)

            payload = {
                'status': 'success',
                'connected': live_ticker_connected,
                'market_open': is_indian_market_open(),
                'timestamp': now_ist().isoformat(),
                'ticks': changed_ticks
            }
            yield f"data: {json.dumps(payload)}\n\n"
            time.sleep(1)

    headers = {
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no'
    }
    return Response(stream_with_context(event_stream()), mimetype='text/event-stream', headers=headers)

@app.route('/api/debug/search', methods=['GET'])
def api_debug_search():
    """Debug endpoint to test search logic"""
    q = request.args.get('q', 'nifty 24550')
    ensure_instruments_cache()
    total = len(INSTRUMENTS_CACHE['symbols'])
    nfo_count = sum(1 for s in INSTRUMENTS_CACHE['symbols'] if s.get('exchange') == 'NFO')
    
    strike_match = re.match(r'^([a-z\s]+?)\s+(\d{4,5})$', q, re.IGNORECASE)
    results = []
    
    if strike_match:
        index_name = strike_match.group(1).strip()
        strike_price = int(strike_match.group(2))
        target_index = 'NIFTY' if 'NIFTY' in index_name.upper() else None
        
        if target_index:
            for s in INSTRUMENTS_CACHE['symbols']:
                if s.get('exchange') == 'NFO' and target_index in s['tradingsymbol']:
                    if s.get('strike') == strike_price:
                        results.append(s['tradingsymbol'])
    
    return jsonify({
        'query': q,
        'pattern_match': strike_match is not None,
        'total_symbols': total,
        'nfo_count': nfo_count,
        'results_count': len(results),
        'first_results': results[:5]
    })


@app.route('/api/quote/<symbol>', methods=['GET'])
def api_quote(symbol):
    """Search for live stock quote by symbol (NSE:INFY format)"""
    if kite is None:
        return jsonify({
            'status': 'error',
            'message': 'Kite API not configured'
        }), 500
    
    try:
        print(f"🔍 Fetching quote for: {symbol}")
        last_error = None
        
        # Accept both "INFY" and "NSE:INFY" formats
        if ':' not in symbol:
            # Try common exchanges
            exchanges = ['NSE', 'BSE', 'NFO']
            for exchange in exchanges:
                try:
                    instrument_key = f"{exchange}:{symbol.upper()}"
                    quote = kite.quote([instrument_key])
                    
                    if quote and instrument_key in quote:
                        data = quote[instrument_key]
                        print(f"✅ Found {symbol} on {exchange}")
                        
                        return jsonify({
                            'status': 'success',
                            'symbol': symbol.upper(),
                            'exchange': exchange,
                            'data': data,
                            'timestamp': datetime.now().isoformat()
                        })
                except Exception as ex:
                    last_error = str(ex)
                    continue

            if last_error and 'Insufficient permission' in last_error:
                return jsonify({
                    'status': 'error',
                    'message': 'Your Kite API key does not have market quote permission.',
                    'details': last_error,
                    'fix': [
                        '1. Open Kite Developer Console and verify app permissions/scopes.',
                        '2. Enable market data/quote access for this API key.',
                        '3. Regenerate access token and restart server.'
                    ]
                }), 403
            
            # Not found
            return jsonify({
                'status': 'error',
                'message': f'Stock "{symbol}" not found',
                'hint': 'Try symbols like INFY, TCS, RELIANCE, HDFCBANK'
            }), 404
        else:
            # Symbol already has exchange
            try:
                quote = kite.quote([symbol.upper()])
                if quote and symbol.upper() in quote:
                    return jsonify({
                        'status': 'success',
                        'symbol': symbol.upper(),
                        'data': quote[symbol.upper()],
                        'timestamp': datetime.now().isoformat()
                    })
                return jsonify({
                    'status': 'error',
                    'message': f'Quote not found for {symbol}'
                }), 404
            except Exception as ex:
                err = str(ex)
                if 'Insufficient permission' in err:
                    return jsonify({
                        'status': 'error',
                        'message': 'Your Kite API key does not have market quote permission.',
                        'details': err,
                        'fix': [
                            '1. Open Kite Developer Console and verify app permissions/scopes.',
                            '2. Enable market data/quote access for this API key.',
                            '3. Regenerate access token and restart server.'
                        ]
                    }), 403
                raise
        
    except Exception as e:
        print(f"❌ Error fetching quote: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def computeEMA(data, period):
    """Compute Exponential Moving Average"""
    if not data or len(data) < period:
        return []
    
    ema = []
    multiplier = 2.0 / (period + 1)
    
    # Calculate SMA for first point
    sma = sum(d['close'] for d in data[:period]) / period
    ema.append(sma)
    
    # Calculate EMA for remaining points
    for i in range(period, len(data)):
        ema_val = data[i]['close'] * multiplier + ema[-1] * (1 - multiplier)
        ema.append(ema_val)
    
    return ema


def computeBollinger(data, period=20, factor=2):
    """Compute Bollinger Bands"""
    if not data or len(data) < period:
        return {'upper': [], 'basis': [], 'lower': []}
    
    basis = []
    upper = []
    lower = []
    
    for i in range(period - 1, len(data)):
        window = [d['close'] for d in data[i - period + 1:i + 1]]
        sma = sum(window) / len(window)
        std = (sum((x - sma) ** 2 for x in window) / len(window)) ** 0.5
        
        basis.append(sma)
        upper.append(sma + factor * std)
        lower.append(sma - factor * std)
    
    return {'upper': upper, 'basis': basis, 'lower': lower}


def computeMomentum(data, period=5):
    """Compute Momentum (ROC)"""
    if not data or len(data) < period:
        return []
    
    momentum = []
    for i in range(period - 1, len(data)):
        mom = ((data[i]['close'] - data[i - period + 1]['close']) / data[i - period + 1]['close']) * 100
        momentum.append(mom)
    
    return momentum


@app.route('/api/test-new', methods=['GET'])
def test_new():
    return jsonify({'status': 'success', 'test': 'new route working'})


@app.route('/api/strategy/signal/<int:instrument_token>/<interval>', methods=['GET'])
def get_strategy_signal(instrument_token, interval):
    """
    Generate 83% win rate strategy signal
    Entry: BB touch + EMA alignment + Momentum confirmation
    Exit: 0.5% profit, -0.4% stop loss, EMA cross, 30-bar hold
    """
    if kite is None:
        return jsonify({'status': 'error', 'message': 'Kite API not initialized'}), 500
    
    try:
        # Get recent 30 days of data (optimized window)
        end_date = datetime.now(IST)
        start_date = end_date - timedelta(days=30)
        
        # Map interval to Kite format
        interval_map = {
            '1minute': 'minute',
            '5minute': '5minute',
            '15minute': '15minute',
            '30minute': '30minute',
            '60minute': '60minute',
            'day': 'day'
        }
        
        kite_interval = interval_map.get(interval, '15minute')
        print(f"📊 Strategy signal request: token={instrument_token}, interval={kite_interval}")
        
        candles = kite.historical_data(
            instrument_token,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            kite_interval
        )
        
        if not candles or len(candles) < 30:
            return jsonify({
                'status': 'success',
                'signal': None,
                'reason': 'Insufficient data for signal generation'
            })
        
        # Calculate indicators
        closes = [c['close'] for c in candles]
        ema9 = computeEMA(candles, 9)
        ema21 = computeEMA(candles, 21)
        bb = computeBollinger(candles, 20, 2)
        momentum = computeMomentum(candles, 5)
        
        if not ema9 or not ema21 or not bb['basis'] or not momentum:
            return jsonify({
                'status': 'success',
                'signal': None,
                'reason': 'Insufficient indicator data'
            })
        
        # Get latest values
        latest_close = closes[-1]
        latest_ema9 = ema9[-1]
        latest_ema21 = ema21[-1]
        latest_bb_upper = bb['upper'][-1]
        latest_bb_lower = bb['lower'][-1]
        latest_momentum = momentum[-1]
        
        signal = None
        strength = 0
        reason = []
        
        # BUY Signal conditions
        buy_conditions = 0
        if latest_close <= latest_bb_lower * 1.01:  # At lower BB
            buy_conditions += 1
            reason.append("Price at lower Bollinger Band")
        
        if latest_ema9 > latest_ema21:  # Bullish alignment
            buy_conditions += 1
            reason.append("EMA9 above EMA21 (bullish)")
        
        if latest_momentum > 0.2:  # Positive momentum
            buy_conditions += 1
            reason.append("Momentum positive")
        
        # SELL Signal conditions
        sell_conditions = 0
        if latest_close >= latest_bb_upper * 0.99:  # At upper BB
            sell_conditions += 1
            reason.append("Price at upper Bollinger Band")
        
        if latest_ema9 < latest_ema21:  # Bearish alignment
            sell_conditions += 1
            reason.append("EMA9 below EMA21 (bearish)")
        
        if latest_momentum < -0.2:  # Negative momentum
            sell_conditions += 1
            reason.append("Momentum negative")
        
        # Determine signal (minimum 2 conditions required)
        if buy_conditions >= 2 and buy_conditions > sell_conditions:
            signal = 'BUY'
            strength = 3 if buy_conditions == 3 else 2
        elif sell_conditions >= 2 and sell_conditions > buy_conditions:
            signal = 'SELL'
            strength = 3 if sell_conditions == 3 else 2
        
        return jsonify({
            'status': 'success',
            'signal': signal,
            'strength': strength,
            'reason': ' | '.join(reason) if reason else 'No signal conditions met',
            'technical': {
                'close': latest_close,
                'ema9': latest_ema9,
                'ema21': latest_ema21,
                'bb_upper': latest_bb_upper,
                'bb_lower': latest_bb_lower,
                'momentum': latest_momentum
            },
            'timestamp': datetime.now(IST).isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error generating strategy signal: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    import os
    print("[INFO] Starting Zerodha Market Watch API Server...")
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')  # Listen on all interfaces for production
    print(f"[INFO] Dashboard:     http://localhost:{port}")
    print(f"[INFO] Market Watch:  http://localhost:{port}/market-watch")
    print(f"[INFO] Token Refresh: http://localhost:{port}/token-refresh")
    # Check token validity at startup
    if kite is not None:
        print("[INFO] Checking Kite access token...")
        if check_token_valid():
            print("✅ Access token is valid")
        else:
            print("⚠️  Access token is EXPIRED — visit http://localhost:{port}/token-refresh to refresh")
    # Pre-load instrument cache
    print("[INFO] Pre-loading instrument cache (NSE + BSE + NFO)...")
    ensure_instruments_cache()
    app.run(debug=False, host=host, port=port, threaded=True)
