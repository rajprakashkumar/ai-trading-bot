"""Check 120-day data availability"""
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
from kite_config import API_KEY, API_SECRET, ACCESS_TOKEN

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

print('Checking data availability for 120-day backtest...')
print('='*80)

to_date = datetime.now()
from_date = to_date - timedelta(days=120)

print(f'Test Period: {from_date.date()} to {to_date.date()}')
print()

timeframes = ['5minute', '15minute', '30minute', '60minute']
token = 260105  # BANKNIFTY

for tf in timeframes:
    try:
        data = kite.historical_data(token, from_date, to_date, tf)
        if data:
            print(f'{tf:12} | Candles: {len(data):5} | First: {str(data[0]["date"])} | Last: {str(data[-1]["date"])}')
        else:
            print(f'{tf:12} | NO DATA')
    except Exception as e:
        print(f'{tf:12} | ERROR: {str(e)[:50]}')
