import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.dependencies.rate_limit import get_redis
from app.models.user import User
from app.utils.security import get_password_hash
import fakeredis.aioredis


# test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """create fresh test database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """test client with database dependency override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # mock redis to avoid needing real redis for tests
    async def override_get_redis():
        return fakeredis.aioredis.FakeRedis()
    
    app.dependency_overrides[get_redis] = override_get_redis
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """create a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Test User",
        role="user",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_employer(db):
    """create a test employer user"""
    user = User(
        email="employer@example.com",
        username="testemployer",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Test Employer",
        role="employer",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin(db):
    """create a test admin user"""
    user = User(
        email="admin@example.com",
        username="testadmin",
        hashed_password=get_password_hash("AdminPassword123"),
        full_name="Test Admin",
        role="admin",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_token(client, test_user):
    """get auth token for test user"""
    response = client.post(
        "/v1/auth/login",
        json={"username": test_user.username, "password": "TestPassword123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def employer_token(client, test_employer):
    """get auth token for test employer"""
    response = client.post(
        "/v1/auth/login",
        json={"username": test_employer.username, "password": "TestPassword123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client, test_admin):
    """get auth token for test admin"""
    response = client.post(
        "/v1/auth/login",
        json={"username": test_admin.username, "password": "AdminPassword123"}
    )
    return response.json()["access_token"]
