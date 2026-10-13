from fastapi.testclient import TestClient
from makma.api import create_app
from makma.providers import MockProvider

class OfflineSandbox:
    async def health(self): return {"available":False,"detail":"test offline"}
    async def stop_all(self): pass

HEADERS={"X-Makma-Client":"local-console"}


def test_operator_api_controls_and_persistence(settings):
    app=create_app(settings,MockProvider(),OfflineSandbox())
    with TestClient(app) as client:
        assert client.get('/health').json()['database']
        assert len(client.get('/agents').json())>=48
        assert client.post('/world/resume',json={}).status_code==403
        assert client.post('/world/resume',json={},headers={**HEADERS,"origin":"https://attacker.example"}).status_code==403
        assert client.post('/world/resume',json={},headers=HEADERS).json()=={"paused":False}
        assert client.post('/world/stop',json={},headers=HEADERS).json()['stopped']
        assert client.get('/agents/missing/memory').status_code==404
        p=client.post('/research/projects',json={"title":"Test retrieval","question":"Can ranking improve on a lexical baseline?"},headers=HEADERS).json()
        assert p['status']=='draft'
        assert client.post('/research/projects/'+p['id']+'/start',json={},headers=HEADERS).status_code==200
        assert client.get('/metrics').json()['hypotheses']==0
        assert client.get('/discoveries').json()==[]
        assert client.get('/metrics',headers={"Host":"evil.example"}).status_code==400
