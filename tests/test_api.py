# Import the module (not the class name) so pytest does not try to collect
# fastapi's `TestClient` as a test class.
from fastapi import testclient
from backend.main import app
client=testclient.TestClient(app)
def test_health(): assert client.get('/api/health').status_code == 200
def test_frontend_and_api_route_order(): assert client.get('/').status_code == 200
