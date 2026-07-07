import re
import calendar
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

def parse_derivative_search(query):
    """Debug version to see what patterns are generated."""
    q = query.strip()
    
    idx_map = {
        'NIFTY': 'NIFTY',
        'BANKNIFTY': 'BANKNIFTY',
        'BANK': 'BANKNIFTY',
        'FINNIFTY': 'FINNIFTY',
        'FIN': 'FINNIFTY',
    }

    month_map = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }

    pattern = r'^([a-zA-Z\s]+?)\s+(\d{4,5})(?:\s+([a-zA-Z]+)\s*(\d{1,2})?)?(?:\s+(CE|PE|FUT))?$'
    match = re.match(pattern, q.upper())
    
    if not match:
        return []

    idx_str, strike_str, month_str, day_str, opt_type = match.groups()
    
    idx_str = idx_str.strip()
    strike = int(strike_str)
    target_day = int(day_str) if day_str else None
    
    print(f"Parsed: idx={idx_str}, strike={strike}, month={month_str}, day={target_day}, type={opt_type}")
    
    # Map index
    idx_key = None
    for key in idx_map:
        if key in idx_str:
            idx_key = idx_map[key]
            break
    
    if not idx_key:
        print(f"Could not map index: {idx_str}")
        return []
    
    print(f"Mapped to: {idx_key}")
    
    # Parse month
    today = datetime.now(IST)
    target_year = today.year
    target_month = None
    
    if month_str:
        month_upper = month_str[:3].upper()
        target_month = month_map.get(month_upper)
        if not target_month:
            print(f"Could not parse month: {month_str}")
            return []
    
    print(f"Target: year={target_year}, month={target_month}, day={target_day}")
    
    # Generate patterns
    patterns = []
    for year_offset in range(3):
        y = target_year + year_offset
        m = target_month
        
        if target_day:
            date_str = f"{y % 100:02d}{m:02d}{target_day:02d}"
            base = f"{idx_key}{date_str}{strike:05d}"
            patterns.extend([base + 'CE', base + 'PE', base + 'FUT'])
        else:
            max_day = calendar.monthrange(y, m)[1]
            for d in range(1, max_day + 1):
                date_str = f"{y % 100:02d}{m:02d}{d:02d}"
                base = f"{idx_key}{date_str}{strike:05d}"
                patterns.extend([base + 'CE', base + 'PE', base + 'FUT'])
    
    print(f"Generated {len(patterns)} patterns")
    print(f"First 5: {patterns[:5]}")
    return patterns

result = parse_derivative_search("Nifty 24450 july 14")
print(f"\nWould search for: {result[:3]}")
