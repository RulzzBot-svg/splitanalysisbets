import sys
import requests

API_KEY = sys.argv[1] if len(sys.argv) > 1 else ''
URL = 'https://api.football-data.org/v4/matches'
params = {'dateFrom': '2019-01-01', 'dateTo': '2019-12-31'}
headers = {'X-Auth-Token': API_KEY}

print('Requesting', URL, 'with params', params)
try:
    r = requests.get(URL, headers=headers, params=params, timeout=30)
    print('Status:', r.status_code)
    print('Headers:', r.headers)
    print('Body (first 2000 chars):')
    print(r.text[:2000])
except Exception as e:
    print('Error:', e)
