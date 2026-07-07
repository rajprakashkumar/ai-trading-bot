import sys
sys.path.insert(0, 'c:\\AI Trading bot')
from app import parse_derivative_search, INSTRUMENTS_CACHE, ensure_instruments_cache

ensure_instruments_cache()
symbols = INSTRUMENTS_CACHE['symbols']

# Test what parse_derivative_search returns for "nifty"
result = parse_derivative_search("nifty", symbols)
print(f"parse_derivative_search('nifty') returned {len(result)} results")

if result:
    print("First 5 results:")
    for i, r in enumerate(result[:5]):
        print(f"  {i+1}. {r['tradingsymbol']}")
else:
    print("No results from parse_derivative_search for 'nifty'")

# Test with "Nifty 24450 july"
result2 = parse_derivative_search("Nifty 24450 july", symbols)
print(f"\nparse_derivative_search('Nifty 24450 july') returned {len(result2)} results")
if result2:
    print("First 5 results:")
    for i, r in enumerate(result2[:5]):
        print(f"  {i+1}. {r['tradingsymbol']}")
