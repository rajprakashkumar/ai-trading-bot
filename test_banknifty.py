"""
Quick test: 83% strategy on BANKNIFTY 15-minute
"""

from datetime import datetime, timedelta
from kiteconnect import KiteConnect
from kite_config import API_KEY, API_SECRET, ACCESS_TOKEN

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

def get_historical_data(token, from_date, to_date, interval):
    try:
        return kite.historical_data(token, from_date, to_date, interval)
    except:
        return None

def calculate_ema(data, period):
    if len(data) < period:
        return [d['close'] for d in data]
    ema = []
    multiplier = 2 / (period + 1)
    first_ema = sum(d['close'] for d in data[:period]) / period
    ema.append(first_ema)
    for i in range(period, len(data)):
        ema.append(data[i]['close'] * multiplier + ema[-1] * (1 - multiplier))
    return [None] * period + ema

def calculate_bb(data, period=20):
    bb_list = []
    for i in range(len(data)):
        if i < period - 1:
            bb_list.append({'upper': None, 'lower': None, 'middle': None})
        else:
            closes = [d['close'] for d in data[i-period+1:i+1]]
            middle = sum(closes) / period
            variance = sum((c - middle)**2 for c in closes) / period
            std = variance ** 0.5
            bb_list.append({'middle': middle, 'upper': middle + (std * 2), 'lower': middle - (std * 2)})
    return bb_list

def calculate_momentum(data, period=5):
    momentum = []
    for i in range(len(data)):
        if i < period:
            momentum.append(0)
        else:
            change = (data[i]['close'] - data[i-period]['close']) / data[i-period]['close'] * 100
            momentum.append(change)
    return momentum

print('=' * 120)
print('BANKNIFTY 15-minute Test with 83% Strategy')
print('=' * 120)

to_date = datetime.now()
from_date = to_date - timedelta(days=30)

data = get_historical_data(260105, from_date, to_date, '15minute')

if data and len(data) > 50:
    print(f'\nTesting BANKNIFTY 15-minute ({len(data)} candles)')
    print('-' * 120)
    
    ema_9 = calculate_ema(data, 9)
    ema_21 = calculate_ema(data, 21)
    bb = calculate_bb(data, 20)
    momentum = calculate_momentum(data, 5)
    
    trades = []
    in_trade = False
    entry_price = None
    entry_bar = None
    entry_direction = None
    
    for i in range(25, len(data) - 1):
        close = data[i]['close']
        high = data[i]['high']
        low = data[i]['low']
        
        if not in_trade:
            entry_signal = None
            strength = 0
            
            if bb[i]['lower'] is not None:
                if ema_9[i] and ema_21[i]:
                    if low <= bb[i]['lower'] and ema_9[i] > ema_21[i] and momentum[i] > 0.2:
                        entry_signal = 1
                        strength = 3
                    elif close < bb[i]['middle'] and ema_9[i] > ema_21[i] and momentum[i] > 0:
                        entry_signal = 1
                        strength = 2
                    elif high >= bb[i]['upper'] and ema_9[i] < ema_21[i] and momentum[i] < -0.2:
                        entry_signal = -1
                        strength = 3
                    elif close > bb[i]['middle'] and ema_9[i] < ema_21[i] and momentum[i] < 0:
                        entry_signal = -1
                        strength = 2
            
            if entry_signal and strength >= 2:
                in_trade = True
                entry_price = close
                entry_bar = i
                entry_direction = entry_signal
        
        else:
            profit_pct = ((close - entry_price) / entry_price) * 100
            hold_bars = i - entry_bar
            profit_target = 0.5
            stop_loss = -0.4
            
            should_exit = False
            exit_reason = None
            
            if entry_direction == 1 and close >= entry_price * (1 + profit_target / 100):
                should_exit = True
                exit_reason = 'PROFIT_TARGET'
            elif entry_direction == -1 and close <= entry_price * (1 - profit_target / 100):
                should_exit = True
                exit_reason = 'PROFIT_TARGET'
            elif entry_direction == 1 and close <= entry_price * (1 + stop_loss / 100):
                should_exit = True
                exit_reason = 'STOP_LOSS'
            elif entry_direction == -1 and close >= entry_price * (1 - stop_loss / 100):
                should_exit = True
                exit_reason = 'STOP_LOSS'
            elif entry_direction == 1 and ema_9[i] and ema_21[i]:
                if i > 0 and ema_9[i-1] > ema_21[i-1] and ema_9[i] <= ema_21[i]:
                    should_exit = True
                    exit_reason = 'EMA_CROSS'
            elif entry_direction == -1 and ema_9[i] and ema_21[i]:
                if i > 0 and ema_9[i-1] < ema_21[i-1] and ema_9[i] >= ema_21[i]:
                    should_exit = True
                    exit_reason = 'EMA_CROSS'
            elif hold_bars > 100:
                should_exit = True
                exit_reason = 'MAX_HOLD'
            
            if should_exit:
                if abs(profit_pct) >= 0.1:
                    trades.append({
                        'entry': entry_price,
                        'exit': close,
                        'profit_pct': profit_pct,
                        'bars': hold_bars,
                        'reason': exit_reason
                    })
                in_trade = False
                entry_price = None
                entry_bar = None
                entry_direction = None
    
    if trades:
        wins = sum(1 for t in trades if t['profit_pct'] > 0)
        losses = sum(1 for t in trades if t['profit_pct'] <= 0)
        wr = (wins / len(trades)) * 100
        total_profit = sum(t['profit_pct'] for t in trades)
        avg_profit = total_profit / len(trades)
        
        win_profit = sum(abs(t['profit_pct']) for t in trades if t['profit_pct'] > 0)
        loss_profit = sum(abs(t['profit_pct']) for t in trades if t['profit_pct'] <= 0)
        pf = win_profit / loss_profit if loss_profit > 0 else 0
        
        emoji = '🏆🏆🏆' if wr >= 85 else '🏆🏆' if wr >= 80 else '🏆' if wr >= 70 else '📊'
        status = 'ACHIEVED 85%+!' if wr >= 85 else '80%+!' if wr >= 80 else '70%+' if wr >= 70 else 'In progress'
        
        print(f'\n{emoji} {status}\n')
        print(f'Win Rate:        {wr:6.2f}%')
        print(f'Trades:          {len(trades):3} (W: {wins:2}  L: {losses:2})')
        print(f'Avg Profit:      {avg_profit:7.3f}%')
        print(f'Total P&L:       {total_profit:7.2f}%')
        print(f'Max Profit/Loss: {max(t["profit_pct"] for t in trades):7.2f}% / {min(t["profit_pct"] for t in trades):7.2f}%')
        print(f'Profit Factor:   {pf:7.2f}')
        print(f'Avg Hold:        {sum(t["bars"] for t in trades)/len(trades):7.1f} bars')
    else:
        print('No trades generated')
else:
    print(f'No data: {len(data) if data else 0} candles')
