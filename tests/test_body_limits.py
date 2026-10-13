from fastapi.testclient import TestClient
from makma.api import create_app
from makma.providers import MockProvider


class OfflineSandbox:
    async def health(self): return {'available':False,'detail':'test offline'}
    async def stop_all(self): pass


def test_chunked_body_rejected_at_actual_byte_limit(settings):
    app=create_app(settings,MockProvider(),OfflineSandbox())
    with TestClient(app) as client:
        chunks=iter([b'{"title":"',b'x'*16000,b'x'*16000,b'"}'])
        response=client.post('/agents',content=chunks,headers={'X-Makma-Client':'local-console','Content-Type':'application/json'})
        assert response.status_code==413
