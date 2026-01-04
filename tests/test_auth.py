import pytest
from fastapi import status


@pytest.mark.auth
class TestAuthentication:
    """test authentication endpoints"""
    
    def test_register_user_success(self, client):
        """test successful user registration"""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "NewPassword123",
                "full_name": "New User",
                "role": "user"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "hashed_password" not in data
    
    def test_register_duplicate_email(self, client, test_user):
        """test registration with duplicate email fails"""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": test_user.email,
                "username": "differentusername",
                "password": "Password123",
                "role": "user"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email already registered" in response.json()["message"].lower()
    
    def test_register_duplicate_username(self, client, test_user):
        """test registration with duplicate username fails"""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "different@example.com",
                "username": test_user.username,
                "password": "Password123",
                "role": "user"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username already taken" in response.json()["message"].lower()
    
    def test_register_weak_password(self, client):
        """test registration with weak password fails"""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "weak",
                "role": "user"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_success(self, client, test_user):
        """test successful login"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": test_user.username,
                "password": "TestPassword123"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user):
        """test login with wrong password fails"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": test_user.username,
                "password": "WrongPassword123"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client):
        """test login with nonexistent user fails"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "Password123"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user(self, client, user_token, test_user):
        """test getting current user info with valid token"""
        response = client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
    
    def test_get_current_user_no_token(self, client):
        """test getting current user without token fails"""
        response = client.get("/v1/auth/me")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_current_user_invalid_token(self, client):
        """test getting current user with invalid token fails"""
        response = client.get(
            "/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
