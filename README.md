# Zerodha Real-Time Holdings Dashboard

A live-syncing dashboard that displays your Zerodha holdings with real-time updates via the Kite MCP server.

## Setup Instructions

### 0. Install Python (if not already installed)

1. Download Python 3.11+ from https://www.python.org/downloads/
2. Run the installer
3. **IMPORTANT**: Check "Add Python to PATH" during installation
4. Restart your terminal/PowerShell after installation
5. Verify: Run `python --version` in PowerShell

### 1. Install Python Dependencies

Run this command once:
```bash
python -m pip install -r requirements.txt
```

Or double-click `run_server.bat` (Windows) which will install dependencies and start the server automatically.

### 2. Start the Backend Server

**Option A: Windows (Easy)**
- Double-click `run_server.bat`

**Option B: PowerShell**
```powershell
python app.py
```

**Option C: Command Prompt**
```cmd
python app.py
```

The server will start at `http://localhost:5000`

### 3. Open the Dashboard

Once the backend server is running, open the live dashboard in your browser:

**File:** `dashboard_live.html`

Just double-click it or open in your browser:
```
file:///c:/AI%20Trading%20bot/dashboard_live.html
```

## Features

✅ **Real-Time Sync** - Data refreshes every 30 seconds from Zerodha  
✅ **Live Connection Status** - Green indicator when connected, red when offline  
✅ **Portfolio Summary** - Total value, P&L, gains/losses  
✅ **Interactive Charts** - P&L distribution and top gainers visualization  
✅ **Search & Sort** - Filter by symbol, sort by P&L, quantity, or alphabetically  
✅ **Responsive Design** - Works on desktop and mobile  
✅ **Auto-Refresh** - Countdown timer to next update  

## API Endpoints

The backend exposes these endpoints:

- `GET /api/holdings` - Get all holdings with summary stats
- `GET /api/health` - Health check
- `GET /api/search/<query>` - Search holdings by symbol
- `GET /api/history/<instrument_token>/<interval>` - Historical candles

History API notes:

- Supports `range` values such as `1D/5D/1M/3M/6M/1Y/3Y/5Y` and also `ALL`/`MAX`.
- Supports explicit window with `from` and `to` in `YYYY-MM-DD HH:MM:SS`.
- The server automatically fetches data in chunks and stitches responses, so requests are not limited by a single-call day cap.

Examples:

```powershell
# Full available history (chunked on server)
http://127.0.0.1:5000/api/history/256265/5minute?range=ALL

# Explicit date window
http://127.0.0.1:5000/api/history/256265/5minute?from=2020-01-01%2009:15:00&to=2026-07-03%2015:30:00
```

## Strategy Backtesting

You can backtest the chart signal strategy from the terminal using `backtest_signals.py`.

Example:

```powershell
python backtest_signals.py --instrument-token 2707457 --interval 5minute --range 3M --time-filter --oi-confirm --writing-confirm --news-clear --vix-state stable --allow-ce --allow-pe
```

Outputs:

- `backtest_trades.csv` - Trade-by-trade log
- `backtest_summary.json` - Aggregated metrics (win rate, drawdown, P&L)

Useful flags:

- `--capital 100000` Starting capital
- `--risk-per-trade 0.01` Risk per trade (1%)
- `--max-trades-per-day 2` Daily trade cap
- `--max-consecutive-losses 2` Stop day after consecutive losses
- `--score-threshold 85` Minimum strategy score
- `--option-beta 3.0` Underlying-to-option move multiplier (proxy model)

Note:

- Backtest uses underlying candle data and an option move proxy (`option-beta`).
- OI/writing/news/VIX are controlled by backtest flags unless you wire live data sources.

## Multi-Strategy Sweep

To compare multiple popular technical strategies in one run, use:

```powershell
python strategy_sweep_backtest.py --instrument-token 256265 --interval 5minute --range 3M --min-trades 20 --top 10
```

This tests a parameter grid across:

- EMA crossover
- RSI mean reversion
- Bollinger mean reversion
- Donchian breakout
- VWAP + EMA + RSI trend logic

Outputs:

- `strategy_sweep_results.csv` - all tested configurations
- `strategy_sweep_best.json` - top-ranked results

Important:

- A 95% win rate is usually not realistic for robust, out-of-sample intraday systems.
- Compare `win_rate_pct` with `total_r` and `max_drawdown_r`; high win rate alone can still lose money.

## How It Works

1. **Backend (app.py)**
   - Flask server running on port 5000
   - Calls Kite MCP server to fetch live holdings
   - Calculates P&L and other metrics
   - Serves data as JSON API

2. **Frontend (dashboard_live.html)**
   - Fetches data from backend API every 30 seconds
   - Displays real-time charts and tables
   - Shows connection status
   - Allows manual refresh

## Troubleshooting

### "Failed to connect" error
- Make sure the backend server is running (`run_server.bat`)
- Check if Python is installed: `python --version`
- Port 5000 must be available

### No data showing
- Have you logged in to Kite via the `/mcp` command in VS Code Chat?
- Check the browser console for errors (F12 → Console tab)

### Server won't start
- Install missing dependencies: `pip install -r requirements.txt`
- Check if port 5000 is already in use
- Try running as Administrator

## Requirements

- Python 3.7+
- Flask and dependencies (see requirements.txt)
- Zerodha Kite account (already logged in via MCP)
- Modern web browser

## Files

- `app.py` - Backend Flask server
- `dashboard_live.html` - Frontend dashboard
- `requirements.txt` - Python dependencies
- `run_server.bat` - Quick start script for Windows
- `holdings_dashboard.html` - Static version (non-live)
