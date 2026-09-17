import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_patient():
    return {
        "resourceType": "Patient",
        "name": [{"family": "Kumar", "given": ["Arun"]}],
        "gender": "male",
        "birthDate": "1995-05-10"
    }
