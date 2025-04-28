import pytest

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from iee305.main import app, get_session

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

from iee305.main import Satellite

def test_get_satellite(session: Session, client: TestClient):
    test_sat = Satellite(acronym="Landsat-7", mass=2100, power=1980)
    session.add(test_sat)
    session.commit()
    session.refresh(test_sat)

    response = client.get(f"/satellites/{test_sat.id}")
    data = response.json()
    assert data["acronym"] == test_sat.acronym
    assert data["mass"] == test_sat.mass
    assert data["power"] == test_sat.power

def test_get_missing_satellite(session: Session, client: TestClient):
    response = client.get(f"/satellites/1")
    assert response.status_code == 404