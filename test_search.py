import requests
import json

# Test 1: Simple prefix search
r = requests.get('http://localhost:5000/api/suggest/NIFTY')
d = r.json()
print(f"Simple 'NIFTY' search: {len(d['results'])} results")
if d['results']:
    print("  First 5:", [x['tradingsymbol'] for x in d['results'][:5]])

# Test 2: Derivative pattern search
r2 = requests.get('http://localhost:5000/api/suggest/Nifty%2024450%20july%2014')
d2 = r2.json()
print(f"\nDerivative 'Nifty 24450 july 14' search: {len(d2['results'])} results")
if d2['results']:
    print("  Results:", [x['tradingsymbol'] for x in d2['results']])
else:
    print("  NO RESULTS!")

# Test 3: Try another derivative search
r3 = requests.get('http://localhost:5000/api/suggest/bank%2044000%20july')
d3 = r3.json()
print(f"\nDerivative 'bank 44000 july' search: {len(d3['results'])} results")
if d3['results']:
    print("  First 5:", [x['tradingsymbol'] for x in d3['results'][:5]])
