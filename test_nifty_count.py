import sys
sys.path.insert(0, 'c:\\AI Trading bot')
from app import INSTRUMENTS_CACHE, ensure_instruments_cache

ensure_instruments_cache()
symbols = INSTRUMENTS_CACHE['symbols']

# Count NIFTY symbols
nifty_all = [s['tradingsymbol'] for s in symbols if 'NIFTY' in s['tradingsymbol']]
print(f'Total NIFTY symbols: {len(nifty_all)}')
print(f'Search limit: 50 results per query')
print()
print('If user searches "nifty":')
print(f'  - Can show: 50 out of {len(nifty_all)} NIFTY symbols')
print(f'  - Missing: {len(nifty_all) - 50} symbols')
print()
print('Sample NIFTY symbols:')
for i, sym in enumerate(nifty_all[:10]):
    print(f'  {i+1}. {sym}')
