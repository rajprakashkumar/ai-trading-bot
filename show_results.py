import json

with open('backtest_simple_effective_results.json') as f:
    data = json.load(f)

nifty15 = data['NIFTY50']['15minute']

print('=' * 60)
print('   83% WIN RATE BACKTEST RESULTS')
print('=' * 60)
print(f'Symbol:          NIFTY50')
print(f'Interval:        15-minute')
print(f'Period:          Recent 30 days')
print()
print(f'Win Rate:        {nifty15["win_rate"]}%')
print(f'Total Trades:    {nifty15["total_trades"]} (W: {nifty15["wins"]}, L: {nifty15["losses"]})')
print(f'Avg Profit:      {nifty15["avg_profit_pct"]}%')
print(f'Total P&L:       {nifty15["total_profit_pct"]}%')
print(f'Max Profit:      {nifty15["max_profit"]}%')
print(f'Max Loss:        {nifty15["max_loss"]}%')
print(f'Profit Factor:   {nifty15["profit_factor"]}')
print(f'Avg Hold:        {nifty15["avg_hold_bars"]} bars (~{nifty15["avg_hold_bars"]*15:.0f} min)')
print()
print('-' * 60)
print('  INDIVIDUAL TRADES')
print('-' * 60)
for i, t in enumerate(nifty15['trades']):
    status = 'WIN' if t['profit_pct'] > 0 else 'LOSS'
    print(f'Trade {i+1} [{status}]: Entry {t["entry"]:,.2f} -> Exit {t["exit"]:,.2f} | P&L: {t["profit_pct"]:+.3f}% | {t["bars"]} bars | {t["reason"]}')
print('=' * 60)
