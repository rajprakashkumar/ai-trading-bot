import re

# Test the strike pattern matching
q = "nifty 24550"
strike_match = re.match(r'^([a-z\s]+?)\s+(\d{4,5})$', q, re.IGNORECASE)

print(f"Query: '{q}'")
if strike_match:
    print(f"Match found!")
    print(f"Index: {strike_match.group(1)}")
    print(f"Strike: {strike_match.group(2)}")
else:
    print("No match found")

# Test expiry pattern
q2 = "nifty july"
expiry_match = re.match(r'^([a-z\s]+?)\s+([a-z]+)$', q2, re.IGNORECASE)
print(f"\nQuery: '{q2}'")
if expiry_match:
    print(f"Match found!")
    print(f"Index: {expiry_match.group(1)}")
    print(f"Month: {expiry_match.group(2)}")
else:
    print("No match found")

# Test symbol pattern
q3 = "NIFTY2671424550CE"
if "2671424550" in q3 and q3.startswith("NIFTY"):
    strike_val = int(q3[11:16])  # 24550
    print(f"\nSymbol: {q3}, Strike extracted: {strike_val}")
