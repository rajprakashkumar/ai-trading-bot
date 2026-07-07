import urllib.request, json

def test(label, q):
    url = 'http://localhost:5000/api/suggest/' + q.replace(' ', '%20')
    with urllib.request.urlopen(url) as r:
        data = json.loads(r.read())
    results = data.get('results', [])
    print(f'[{label}]: {len(results)} results')
    for item in results[:5]:
        ts = item['tradingsymbol']
        itype = item['instrument_type']
        expiry = item['expiry']
        strike = item['strike']
        print(f'  {ts} | {itype} | expiry={expiry} | strike={strike}')
    print()

print('=== Test 1: Strike search "nifty 24550" ===')
test('nifty 24550', 'nifty 24550')

print('=== Test 2: Expiry search "nifty july" ===')
test('nifty july', 'nifty july')

print('=== Test 3: Substring "infy" ===')
test('infy', 'infy')

print('=== Test 4: Bank nifty strike "bank 58300" ===')
test('bank 58300', 'bank 58300')
