import sys
import re
sys.path.insert(0, 'c:\\AI Trading bot')
from app import INSTRUMENTS_CACHE, ensure_instruments_cache

ensure_instruments_cache()
symbols = INSTRUMENTS_CACHE['symbols']

# Test strike search "nifty 24550"
q = "nifty 24550"
q_upper = q.upper()
strike_match = re.match(r'^([a-z\s]+?)\s+(\d{4,5})$', q, re.IGNORECASE)

if strike_match:
    index_name = strike_match.group(1).strip()
    strike_price = int(strike_match.group(2))
    
    print(f"Searching for: {index_name} with strike {strike_price}")
    
    # Map index names
    index_map = {
        'NIFTY': 'NIFTY', 'NIFTY50': 'NIFTY',
        'BANKNIFTY': 'BANKNIFTY', 'BANK': 'BANKNIFTY',
        'FINNIFTY': 'FINNIFTY', 'FIN': 'FINNIFTY',
        'SENSEX': 'SENSEX', 'MIDCPNIFTY': 'MIDCPNIFTY', 'MIDCAP': 'MIDCPNIFTY'
    }
    
    target_index = None
    for key in index_map:
        if key in index_name.upper():
            target_index = index_map[key]
            break
    
    print(f"Mapped to: {target_index}")
    
    results = []
    if target_index:
        # Find all options/futures with this strike
        for s in symbols:
            if s.get('exchange') == 'NFO' and target_index in s['tradingsymbol']:
                # Check if strike matches
                if s.get('strike') == strike_price or (strike_price and f'{int(strike_price):05d}' in s['tradingsymbol']):
                    results.append(s)
    
    print(f"Found {len(results)} results")
    
    if results:
        print("First 5:")
        for r in results[:5]:
            print(f"  {r['tradingsymbol']} - Strike: {r['strike']}, Type: {r['instrument_type']}")
