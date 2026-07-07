"""Test the strike search logic exactly as it runs in app.py"""
import json
import re
import sys

# Load cache exactly as app.py does
with open('instruments_cache.json', 'r', encoding='utf-8') as f:
    cache_data = json.load(f)

INSTRUMENTS_CACHE = {
    'loaded': True,
    'symbols': cache_data['symbols']
}

def simulate_search(query):
    q = query.strip()
    results = []
    q_upper = q.upper()

    # PATTERN 1: Strike-based search "NIFTY 24550"
    strike_match = re.match(r'^([a-z\s]+?)\s+(\d{4,5})$', q, re.IGNORECASE)
    print(f'Strike match: {strike_match is not None}')
    
    if strike_match:
        index_name = strike_match.group(1).strip()
        strike_price = int(strike_match.group(2))
        print(f'  Index: {index_name!r}, Strike: {strike_price}')
        
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
        
        print(f'  Mapped to: {target_index}')
        
        if target_index:
            for s in INSTRUMENTS_CACHE['symbols']:
                if s.get('exchange') == 'NFO' and target_index in s['tradingsymbol']:
                    if s.get('strike') == strike_price:
                        results.append(s)
            print(f'  Found by strike field: {len(results)}')
            
            # Also check by symbol substring
            results2 = []
            strike_str = f'{int(strike_price):05d}'
            for s in INSTRUMENTS_CACHE['symbols']:
                if s.get('exchange') == 'NFO' and target_index in s['tradingsymbol']:
                    if strike_str in s['tradingsymbol']:
                        results2.append(s)
            print(f'  Found by symbol substring ({strike_str}): {len(results2)}')
    
    if not results:
        # Fall back to substring
        for s in INSTRUMENTS_CACHE['symbols']:
            ts = s.get('tradingsymbol', '').upper()
            if ts.startswith(q_upper) or q_upper in ts:
                results.append(s)
                if len(results) >= 5:
                    break
        print(f'  Fallback substring: {len(results)}')
    
    return results[:5]

print('=== Test: nifty 24550 ===')
r = simulate_search('nifty 24550')
for x in r:
    print(f'  Result: {x["tradingsymbol"]} strike={x.get("strike")}')

print()
print('=== Test: nifty july ===')

q = 'nifty july'
expiry_match = re.match(r'^([a-z\s]+?)\s+([a-z]+)$', q, re.IGNORECASE)
print(f'Expiry match: {expiry_match is not None}')
if expiry_match:
    index_name = expiry_match.group(1).strip()
    month_name = expiry_match.group(2).strip()
    print(f'  Index: {index_name!r}, Month: {month_name!r}')
    month_short = month_name[:3].upper()
    print(f'  Month short: {month_short}')
    # Find by month in symbol
    index_map = {'NIFTY': 'NIFTY'}
    target_index = 'NIFTY'
    month_results = [s for s in INSTRUMENTS_CACHE['symbols'] 
                     if s.get('exchange') == 'NFO' 
                     and target_index in s['tradingsymbol']
                     and month_short in s['tradingsymbol']]
    print(f'  Found: {len(month_results)}')
    for x in month_results[:3]:
        print(f'  Result: {x["tradingsymbol"]}')
