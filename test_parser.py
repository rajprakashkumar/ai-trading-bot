import sys
sys.path.insert(0, 'c:\\AI Trading bot')

from app import INSTRUMENTS_CACHE, ensure_instruments_cache, parse_derivative_search

# Ensure cache is loaded
ensure_instruments_cache()

print(f"Cache loaded: {INSTRUMENTS_CACHE['loaded']}")
print(f"Total symbols: {len(INSTRUMENTS_CACHE['symbols'])}")

# Check if the specific instrument exists
nifty_search = [s for s in INSTRUMENTS_CACHE['symbols'] if s['tradingsymbol'] == 'NIFTY2671424450CE']
print(f"\nNIFTY2671424450CE exists: {len(nifty_search) > 0}")

# Try parsing
result = parse_derivative_search("Nifty 24450 july 14", INSTRUMENTS_CACHE['symbols'])
print(f"\nDerivative search result: {len(result)} items")
if result:
    print("Results:", [r['tradingsymbol'] for r in result])
