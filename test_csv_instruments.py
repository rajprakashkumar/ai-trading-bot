import pandas as pd

print('Downloading instruments CSV from Kite (no auth needed)...')
df = pd.read_csv('https://api.kite.trade/instruments')
print(f'Total rows: {len(df)}')
print(f'Columns: {list(df.columns)}')
print()

# Save to file
df.to_csv('instruments.csv', index=False)
print('Saved to instruments.csv')
print()

nfo = df[df['exchange'] == 'NFO']
print(f'NFO instruments: {len(nfo)}')
print()

# Test 1: strike search "nifty 24550"
nifty_24550 = nfo[
    (nfo['tradingsymbol'].str.startswith('NIFTY')) &
    (nfo['strike'] == 24550.0)
]
print(f'Strike search [nifty 24550]: {len(nifty_24550)} results')
print(nifty_24550[['tradingsymbol', 'instrument_type', 'expiry', 'strike']].head(10).to_string())
print()

# Test 2: expiry search "nifty july"
nifty_jul = nfo[
    nfo['tradingsymbol'].str.startswith('NIFTY') &
    nfo['tradingsymbol'].str.contains('JUL', case=False)
]
print(f'Expiry search [nifty july]: {len(nifty_jul)} results')
print(nifty_jul[['tradingsymbol', 'instrument_type', 'expiry', 'strike']].head(8).to_string())
print()

# Test 3: bank nifty strike
bank_44000 = nfo[
    (nfo['tradingsymbol'].str.startswith('BANKNIFTY')) &
    (nfo['strike'] == 44000.0)
]
print(f'Strike search [bank 44000]: {len(bank_44000)} results')
print(bank_44000[['tradingsymbol', 'instrument_type', 'expiry', 'strike']].head(6).to_string())
print()

# Show data types
print(f'strike dtype: {df["strike"].dtype}')
