import json
import re

# Load cache
with open('instruments_cache.json', 'r', encoding='utf-8') as f:
    instruments = json.load(f)

print(f'Total instruments: {len(instruments)}')

# Get NFO sample
nfo = [x for x in instruments if x.get('exchange') == 'NFO']
print(f'NFO count: {len(nfo)}')

# Sample keys
if nfo:
    print(f'Sample keys: {list(nfo[0].keys())}')
    print(f'Sample item: {nfo[0]}')

# Check the INSTRUMENTS_CACHE structure
# The endpoint uses INSTRUMENTS_CACHE['symbols'] - check if it stores list of dicts
# First item
print(f'\nFirst instrument: {instruments[0]}')

# Test strike field values
nifty_nfo = [x for x in instruments if x.get('exchange') == 'NFO' and 'NIFTY' in x.get('tradingsymbol', '')]
print(f'\nNIFTY NFO count: {len(nifty_nfo)}')
print(f'First NIFTY NFO: {nifty_nfo[0] if nifty_nfo else "none"}')

# Strike value type
strikes = [x.get('strike') for x in nifty_nfo[:5]]
print(f'Strike values: {strikes}')
print(f'Strike types: {[type(s).__name__ for s in strikes]}')

# Search for 24550 strike
found = [x for x in nifty_nfo if x.get('strike') == 24550.0 or x.get('strike') == 24550]
print(f'Found by strike==24550: {len(found)}')
for item in found[:5]:
    print(f'  {item["tradingsymbol"]} strike={item.get("strike")}')
