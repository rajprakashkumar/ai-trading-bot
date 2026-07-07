import urllib.request, json

def test(q):
    url = f'http://localhost:5000/api/suggest/{urllib.request.quote(q)}'
    with urllib.request.urlopen(url) as r:
        data = json.loads(r.read())
    results = data['results']
    
    futs = [r for r in results if r['instrument_type']=='FUT']
    opts_ce = [r for r in results if r['instrument_type']=='CE']
    opts_pe = [r for r in results if r['instrument_type']=='PE']
    
    print(f"Query: {q}")
    print(f"  Total: {len(results)}, Futures: {len(futs)}, CE: {len(opts_ce)}, PE: {len(opts_pe)}")
    if futs:
        for f in futs:
            print(f"    FUT: {f['tradingsymbol']} - {f['expiry']}")
    print()

test('nifty july')
test('nifty 25500 july')
test('nifty july 25500')
test('nifty august')
test('bank august')
test('nifty september')

