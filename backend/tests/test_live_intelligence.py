"""
Backend tests for SwarmSim Live Intelligence feature
Tests the /fetch-live endpoint and related functionality
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndSession:
    """Basic health and session tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is working"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("Health endpoint: PASSED")
    
    def test_create_session(self):
        """Test session creation"""
        response = requests.post(f"{BASE_URL}/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0
        print(f"Session created: {data['session_id']}")
        return data["session_id"]
    
    def test_get_prediction_horizons(self):
        """Test prediction horizons endpoint"""
        response = requests.get(f"{BASE_URL}/api/prediction-horizons")
        assert response.status_code == 200
        data = response.json()
        assert "horizons" in data
        expected_horizons = [
            "Next 24 hours",
            "Next week",
            "Next month",
            "Next 3 months",
            "Next 6 months",
            "Long term (1+ year)"
        ]
        assert data["horizons"] == expected_horizons
        print(f"Prediction horizons: {data['horizons']}")


class TestLiveIntelligence:
    """Tests for Live Intelligence feature"""
    
    @pytest.fixture
    def session_id(self):
        """Create a session for testing"""
        response = requests.post(f"{BASE_URL}/api/sessions")
        assert response.status_code == 200
        return response.json()["session_id"]
    
    def test_fetch_live_basic(self, session_id):
        """Test basic fetch-live endpoint with a simple topic"""
        payload = {
            "topic": "Bitcoin price",
            "horizon": "Next week",
            "prediction_query": "What will happen to Bitcoin price next week?"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=payload,
            timeout=90
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert data["status"] == "graph_ready"
        assert "topic" in data
        assert data["topic"] == "Bitcoin price"
        assert "graph" in data
        assert "intel_brief" in data
        assert "sources_count" in data
        assert "fetched_at" in data
        
        # Verify graph structure
        graph = data["graph"]
        assert "summary" in graph
        assert "entities" in graph
        assert "relationships" in graph
        assert "themes" in graph
        assert len(graph["entities"]) > 0
        assert len(graph["relationships"]) > 0
        
        # Verify intel_brief structure
        intel_brief = data["intel_brief"]
        assert "summary" in intel_brief
        assert "key_developments" in intel_brief
        assert "stakeholders" in intel_brief
        assert "data_points" in intel_brief
        
        print(f"Fetch live PASSED - {data['sources_count']} sources, {len(graph['entities'])} entities, {len(graph['relationships'])} relationships")
        return data
    
    def test_fetch_live_different_horizons(self, session_id):
        """Test fetch-live with different prediction horizons"""
        horizons = ["Next 24 hours", "Next month", "Long term (1+ year)"]
        
        for horizon in horizons:
            # Create new session for each test
            session_response = requests.post(f"{BASE_URL}/api/sessions")
            new_session_id = session_response.json()["session_id"]
            
            payload = {
                "topic": "US Federal Reserve interest rates",
                "horizon": horizon,
                "prediction_query": ""  # Test auto-generated query
            }
            
            response = requests.post(
                f"{BASE_URL}/api/sessions/{new_session_id}/fetch-live",
                json=payload,
                timeout=90
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "graph_ready"
            print(f"Horizon '{horizon}' test PASSED")
    
    def test_fetch_live_empty_topic_fails(self, session_id):
        """Test that empty topic returns error"""
        payload = {
            "topic": "",
            "horizon": "Next week"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=payload,
            timeout=30
        )
        
        # Should fail validation or return error
        # Empty topic should be rejected
        assert response.status_code in [400, 422]
        print("Empty topic validation: PASSED")
    
    def test_fetch_live_invalid_session(self):
        """Test fetch-live with invalid session ID"""
        payload = {
            "topic": "Test topic",
            "horizon": "Next week"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/sessions/invalid-session-id/fetch-live",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 404
        print("Invalid session validation: PASSED")
    
    def test_session_data_mode_after_live_fetch(self, session_id):
        """Test that session data_mode is set to 'live' after fetch-live"""
        payload = {
            "topic": "AI regulation",
            "horizon": "Next 3 months"
        }
        
        # Fetch live data
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=payload,
            timeout=90
        )
        assert response.status_code == 200
        
        # Get session and verify data_mode
        session_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
        assert session_response.status_code == 200
        session_data = session_response.json()
        
        assert session_data["data_mode"] == "live"
        assert session_data["topic"] == "AI regulation"
        assert session_data["status"] == "graph_ready"
        print("Session data_mode verification: PASSED")


class TestLiveIntelligenceToAgentsFlow:
    """Test the full flow from Live Intelligence to Agent generation"""
    
    def test_full_live_to_agents_flow(self):
        """Test complete flow: fetch-live -> generate-agents"""
        # Create session
        session_response = requests.post(f"{BASE_URL}/api/sessions")
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]
        print(f"Created session: {session_id}")
        
        # Fetch live data
        fetch_payload = {
            "topic": "Tesla stock outlook",
            "horizon": "Next month",
            "prediction_query": "Will Tesla stock go up or down next month?"
        }
        
        fetch_response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=fetch_payload,
            timeout=90
        )
        assert fetch_response.status_code == 200
        fetch_data = fetch_response.json()
        assert fetch_data["status"] == "graph_ready"
        print(f"Live data fetched: {fetch_data['sources_count']} sources")
        
        # Generate agents
        agents_payload = {"num_agents": 10}
        agents_response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/generate-agents",
            json=agents_payload,
            timeout=120
        )
        assert agents_response.status_code == 200
        agents_data = agents_response.json()
        
        assert "agents" in agents_data
        assert len(agents_data["agents"]) == 10
        
        # Verify agent structure
        agent = agents_data["agents"][0]
        assert "id" in agent
        assert "name" in agent
        assert "occupation" in agent
        assert "personality_type" in agent
        assert "initial_stance" in agent
        
        print(f"Generated {len(agents_data['agents'])} agents successfully")
        print("Full live-to-agents flow: PASSED")


class TestDocumentUploadRegression:
    """Regression tests for Document Upload mode"""
    
    def test_upload_endpoint_exists(self):
        """Test that upload endpoint exists and requires file"""
        session_response = requests.post(f"{BASE_URL}/api/sessions")
        session_id = session_response.json()["session_id"]
        
        # Try to call upload without file - should fail with 422
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/upload",
            data={"prediction_query": "Test question"}
        )
        
        # Should fail because no file provided
        assert response.status_code == 422
        print("Upload endpoint validation: PASSED")
    
    def test_session_default_mode_is_upload(self):
        """Test that new sessions default to upload mode"""
        session_response = requests.post(f"{BASE_URL}/api/sessions")
        session_id = session_response.json()["session_id"]
        
        session_data = requests.get(f"{BASE_URL}/api/sessions/{session_id}").json()
        assert session_data["data_mode"] == "upload"
        print("Default data_mode is 'upload': PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
