import json
with open('c:\\temp\\api_response.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

print(f'Total results: {len(data["results"])}')
if data["results"]:
    print(f'First: {data["results"][0]["tradingsymbol"]}')
    print(f'Last: {data["results"][-1]["tradingsymbol"]}')
