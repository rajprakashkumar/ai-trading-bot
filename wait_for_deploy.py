import requests
import time

token = 'rnd_RrYgnJeD7xhXLyASjEUFsT9xx3nf'
service_id = 'srv-d96i7cnavr4c739i4l6g'
url = f'https://api.render.com/v1/services/{service_id}'
headers = {'Authorization': f'Bearer {token}'}

print('\n' + '='*60)
print('WAITING FOR DEPLOYMENT...')
print('='*60 + '\n')

for i in range(60):  # Check for 5 minutes
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        s = r.json()
        status = s.get('status', 'unknown')
        service_url = s.get('serviceUrl', 'building...')
        
        print(f'Attempt {i+1:2d}: Status={status:12s} | URL: {service_url}')
        
        if status == 'live' and service_url != 'building...':
            print('\n' + '='*60)
            print('✓ DEPLOYMENT COMPLETE!')
            print('='*60)
            print(f'\nYour app is LIVE!')
            print(f'\n🌐 URL: {service_url}')
            print(f'📊 Dashboard: {service_url}/market-watch')
            print(f'\nNext: Visit the URL and login to test!')
            print('='*60 + '\n')
            break
    
    time.sleep(5)

else:
    print(f'\n⏱ Deployment still in progress. Check dashboard:')
    print(f'https://dashboard.render.com/web/{service_id}')
