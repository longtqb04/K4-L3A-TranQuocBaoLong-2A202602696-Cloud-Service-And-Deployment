"""Collect real HTTP responses without printing credentials."""
import json
import os
import uuid
import httpx

base = os.getenv('OBSERVE_URL', 'http://nginx')
user = 'exercise-' + uuid.uuid4().hex[:8]
headers = {'X-API-Key': os.environ['AGENT_API_KEY'], 'X-User-Id': user}
with httpx.Client(base_url=base, timeout=60) as client:
    for path in ['/health', '/ready']:
        response = client.get(path)
        print(path, response.status_code, response.text)
    response = client.post('/ask', json={'question': 'Hello'})
    print('no_key', response.status_code, response.text)
    for i in range(12):
        response = client.post('/ask', headers=headers, json={'question': 'Explain deployment'})
        try:
            body = response.json()
        except ValueError:
            body = response.text
        print(json.dumps({'request': i + 1, 'status': response.status_code, 'response': body}))
