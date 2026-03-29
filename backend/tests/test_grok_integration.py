"""
Test suite for Grok (xAI) integration in SwarmSim
Tests health endpoint, session creation, and Grok availability
"""
import pytest
import requests
import os

# Get backend URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthEndpoint:
    """Health endpoint tests - verifies Grok availability"""
    
    def test_health_returns_200(self):
        """Health endpoint should return 200 OK"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✅ Health endpoint returns 200 OK")
    
    def test_health_returns_grok_available_true(self):
        """Health endpoint should return grok_available: true when XAI_API_KEY is set"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        assert "grok_available" in data, "Response missing 'grok_available' field"
        assert data["grok_available"] == True, f"Expected grok_available=true, got {data['grok_available']}"
        print(f"✅ grok_available: {data['grok_available']}")
    
    def test_health_returns_twitter_source_grok(self):
        """Health endpoint should return twitter_source: 'Grok X Search' when Grok is available"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        assert "twitter_source" in data, "Response missing 'twitter_source' field"
        assert data["twitter_source"] == "Grok X Search", f"Expected 'Grok X Search', got '{data['twitter_source']}'"
        print(f"✅ twitter_source: {data['twitter_source']}")
    
    def test_health_returns_status_ok(self):
        """Health endpoint should return status: ok"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data, "Response missing 'status' field"
        assert data["status"] == "ok", f"Expected status='ok', got '{data['status']}'"
        print(f"✅ status: {data['status']}")


class TestSessionEndpoint:
    """Session creation endpoint tests"""
    
    def test_create_session_returns_201_or_200(self):
        """POST /api/sessions should create a new session"""
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=10)
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        print(f"✅ Session creation returns {response.status_code}")
    
    def test_create_session_returns_session_id(self):
        """POST /api/sessions should return a session_id"""
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=10)
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert "session_id" in data, "Response missing 'session_id' field"
        assert isinstance(data["session_id"], str), "session_id should be a string"
        assert len(data["session_id"]) > 0, "session_id should not be empty"
        print(f"✅ session_id: {data['session_id']}")
    
    def test_create_session_returns_uuid_format(self):
        """POST /api/sessions should return a valid UUID"""
        import uuid
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=10)
        assert response.status_code in [200, 201]
        data = response.json()
        
        session_id = data["session_id"]
        try:
            uuid.UUID(session_id)
            print(f"✅ session_id is valid UUID: {session_id}")
        except ValueError:
            pytest.fail(f"session_id is not a valid UUID: {session_id}")
    
    def test_get_session_after_creation(self):
        """GET /api/sessions/{session_id} should return the created session"""
        # Create session
        create_response = requests.post(f"{BASE_URL}/api/sessions", timeout=10)
        assert create_response.status_code in [200, 201]
        session_id = create_response.json()["session_id"]
        
        # Get session
        get_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}", timeout=10)
        assert get_response.status_code == 200, f"Expected 200, got {get_response.status_code}"
        
        data = get_response.json()
        assert data["id"] == session_id, f"Session ID mismatch"
        assert data["status"] == "created", f"Expected status='created', got '{data['status']}'"
        print(f"✅ Session retrieved successfully: {session_id}")


class TestPredictionHorizons:
    """Prediction horizons endpoint tests"""
    
    def test_get_prediction_horizons(self):
        """GET /api/prediction-horizons should return available horizons"""
        response = requests.get(f"{BASE_URL}/api/prediction-horizons", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "horizons" in data, "Response missing 'horizons' field"
        assert isinstance(data["horizons"], list), "horizons should be a list"
        assert len(data["horizons"]) > 0, "horizons should not be empty"
        
        expected_horizons = ["Next 24 hours", "Next week", "Next month"]
        for h in expected_horizons:
            assert h in data["horizons"], f"Missing expected horizon: {h}"
        
        print(f"✅ Prediction horizons: {data['horizons']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
