# File: test_auth_endpoints.py
# Path: /home/herb/Desktop/AndyWeb/Tests/test_auth_endpoints.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-25
# Last Modified: 2025-07-25 09:05AM

"""
Test suite for BowersWorld.com authentication endpoints
Comprehensive testing of user registration, login, and session management
"""

import pytest
import asyncio
import json
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the FastAPI app
import sys
sys.path.append('/home/herb/Desktop/AndyWeb/Source')
from API.MainAPI import App
from Core.DatabaseManager import DatabaseManager

class TestAuthenticationEndpoints:
    """Test suite for authentication endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client with temporary database"""
        # Create temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        # Mock the database path
        with patch('API.MainAPI.PROJECT_PATHS', {'database_path': temp_db_path}):
            client = TestClient(App)
            
            # Initialize test database
            db_manager = DatabaseManager(temp_db_path)
            db_manager.Connect()
            db_manager.InitializeUserTables()
            
            yield client
            
            # Cleanup
            os.unlink(temp_db_path)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            "email": "test@bowersworld.com",
            "password": "testpassword123",
            "username": "testuser",
            "subscription_tier": "free"
        }
    
    def test_user_registration_success(self, client, sample_user_data):
        """Test successful user registration"""
        response = client.post("/api/auth/register", json=sample_user_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert "message" in data
        assert data["user"]["email"] == sample_user_data["email"]
        assert data["user"]["subscription_tier"] == sample_user_data["subscription_tier"]
        assert data["email_verification_required"] is True
    
    def test_user_registration_duplicate_email(self, client, sample_user_data):
        """Test registration with duplicate email"""
        # Register first user
        client.post("/api/auth/register", json=sample_user_data)
        
        # Try to register with same email
        response = client.post("/api/auth/register", json=sample_user_data)
        
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"]
    
    def test_user_registration_invalid_email(self, client, sample_user_data):
        """Test registration with invalid email"""
        sample_user_data["email"] = "invalid-email"
        
        response = client.post("/api/auth/register", json=sample_user_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_user_registration_weak_password(self, client, sample_user_data):
        """Test registration with weak password"""
        sample_user_data["password"] = "weak"
        
        response = client.post("/api/auth/register", json=sample_user_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_user_registration_invalid_subscription_tier(self, client, sample_user_data):
        """Test registration with invalid subscription tier"""
        sample_user_data["subscription_tier"] = "invalid_tier"
        
        response = client.post("/api/auth/register", json=sample_user_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_user_login_success(self, client, sample_user_data):
        """Test successful user login"""
        # Register user first
        client.post("/api/auth/register", json=sample_user_data)
        
        # Login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert "session_token" in data
        assert "refresh_token" in data
        assert "expires_at" in data
        assert data["user"]["email"] == sample_user_data["email"]
    
    def test_user_login_invalid_credentials(self, client, sample_user_data):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@bowersworld.com",
            "password": "wrongpassword"
        }
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_user_login_wrong_password(self, client, sample_user_data):
        """Test login with correct email but wrong password"""
        # Register user first
        client.post("/api/auth/register", json=sample_user_data)
        
        # Login with wrong password
        login_data = {
            "email": sample_user_data["email"],
            "password": "wrongpassword"
        }
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication"""
        response = client.get("/api/auth/profile")
        
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
    
    def test_protected_endpoint_with_auth(self, client, sample_user_data):
        """Test accessing protected endpoint with valid authentication"""
        # Register and login user
        client.post("/api/auth/register", json=sample_user_data)
        
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        login_response = client.post("/api/auth/login", json=login_data)
        token = login_response.json()["session_token"]
        
        # Access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/profile", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user_data["email"]
    
    def test_user_logout(self, client, sample_user_data):
        """Test user logout"""
        # Register and login user
        client.post("/api/auth/register", json=sample_user_data)
        
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        login_response = client.post("/api/auth/login", json=login_data)
        token = login_response.json()["session_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/auth/logout", headers=headers)
        
        assert response.status_code == 200
        assert "Logout successful" in response.json()["message"]
        
        # Try to access protected endpoint with same token
        profile_response = client.get("/api/auth/profile", headers=headers)
        assert profile_response.status_code == 401
    
    def test_session_cleanup_requires_auth(self, client):
        """Test that session cleanup endpoint requires authentication"""
        response = client.post("/api/auth/cleanup-sessions")
        
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
    
    def test_user_stats_requires_auth(self, client):
        """Test that user stats endpoint requires authentication"""
        response = client.get("/api/auth/stats")
        
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

class TestSubscriptionTiers:
    """Test subscription tier functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client with temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        with patch('API.MainAPI.PROJECT_PATHS', {'database_path': temp_db_path}):
            client = TestClient(App)
            
            db_manager = DatabaseManager(temp_db_path)
            db_manager.Connect()
            db_manager.InitializeUserTables()
            
            yield client
            
            os.unlink(temp_db_path)
    
    @pytest.mark.parametrize("tier", ["free", "scholar", "researcher", "institution"])
    def test_valid_subscription_tiers(self, client, tier):
        """Test registration with all valid subscription tiers"""
        user_data = {
            "email": f"test_{tier}@bowersworld.com",
            "password": "testpassword123",
            "subscription_tier": tier
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 200
        assert response.json()["user"]["subscription_tier"] == tier

class TestAccountSecurity:
    """Test account security features"""
    
    @pytest.fixture
    def client(self):
        """Create test client with temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        with patch('API.MainAPI.PROJECT_PATHS', {'database_path': temp_db_path}):
            client = TestClient(App)
            
            db_manager = DatabaseManager(temp_db_path)
            db_manager.Connect()
            db_manager.InitializeUserTables()
            
            yield client
            
            os.unlink(temp_db_path)
    
    def test_account_lockout_after_failed_attempts(self, client):
        """Test account lockout after multiple failed login attempts"""
        # Register user
        user_data = {
            "email": "test@bowersworld.com",
            "password": "correctpassword",
            "subscription_tier": "free"
        }
        client.post("/api/auth/register", json=user_data)
        
        # Attempt login with wrong password multiple times
        login_data = {
            "email": user_data["email"],
            "password": "wrongpassword"
        }
        
        # Make 5 failed attempts (should trigger lockout)
        for i in range(5):
            response = client.post("/api/auth/login", json=login_data)
            assert response.status_code == 401
        
        # 6th attempt should return account locked error
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 423
        assert "locked" in response.json()["detail"].lower()

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])