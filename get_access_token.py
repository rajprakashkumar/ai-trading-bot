from kiteconnect import KiteConnect
from kite_config import API_KEY, API_SECRET

kite = KiteConnect(api_key=API_KEY)
request_token = '057RQgMLeZZXSwKZa3ukjmXyFFYWrWuf'

print('🔄 Exchanging request token for access token...')
print(f'Request Token: {request_token}')
print()

try:
    session = kite.generate_session(request_token, api_secret=API_SECRET)
    access_token = session.get('access_token')
    user_id = session.get('user_id')
    
    print('=' * 60)
    print('✅ SUCCESS!')
    print('=' * 60)
    print()
    print('Update kite_config.py with:')
    print()
    print(f'ACCESS_TOKEN = "{access_token}"')
    print(f'USER_ID = "{user_id}"')
    print()
    
    # Auto-update
    with open('kite_config.py', 'r') as f:
        content = f.read()
    
    content = content.replace(
        'ACCESS_TOKEN = "get_token_using_generate_token.py"',
        f'ACCESS_TOKEN = "{access_token}"'
    )
    content = content.replace(
        'USER_ID = "your_user_id_here"',
        f'USER_ID = "{user_id}"'
    )
    
    with open('kite_config.py', 'w') as f:
        f.write(content)
    
    print('✅ kite_config.py updated!')
    print()
    print('🚀 Flask server should auto-reload...')
    print('Go to http://localhost:5000 to see your REAL holdings!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
