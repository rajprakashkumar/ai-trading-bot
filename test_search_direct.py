import sys
sys.path.insert(0, 'c:\\AI Trading bot')
from app import INSTRUMENTS_CACHE, ensure_instruments_cache

ensure_instruments_cache()
symbols = INSTRUMENTS_CACHE['symbols']

# Simulate search for "nifty"
q = "nifty"
q_upper = q.upper()
results = []

print(f"Searching for '{q}'...")

# Collect all matching instruments
for s in symbols:
    ts = s.get('tradingsymbol', '').upper()
    name = (s.get('name') or '').upper()
    exchange = s.get('exchange', '')
    
    # Only include main exchanges
    if exchange not in ['NSE', 'BSE', 'NFO', 'MCX', 'BFO']:
        continue
        
    # Match by trading symbol or name
    if ts.startswith(q_upper) or q_upper in ts or (name and q_upper in name):
        results.append(s)
        
        # Stop after collecting enough results
        if len(results) >= 250:
            break

print(f"Collected {len(results)} results before sorting")

# Sort: NFO first (derivatives), then stocks
def sort_key(item):
    exch = item.get('exchange', '')
    expiry = item.get('expiry', '')
    itype = item.get('instrument_type', '')
    
    # NFO items (derivatives) should appear first, sorted by expiry
    if exch == 'NFO' and expiry:
        return (0, expiry, itype, item['tradingsymbol'])
    # Other items sorted by exchange and symbol
    return (1, exch, '', item['tradingsymbol'])

results = sorted(results, key=sort_key)[:200]

print(f"Final results: {len(results)}")
print(f"NFO: {len([r for r in results if r.get('exchange') == 'NFO'])}, Stock: {len([r for r in results if r.get('exchange') in ['NSE', 'BSE']])}")

if results:
    print(f"First: {results[0]['tradingsymbol']}")
    print(f"Last: {results[-1]['tradingsymbol']}")
