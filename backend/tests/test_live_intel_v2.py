"""
Backend tests for SwarmSim Live Intelligence feature v2
Tests the updated /fetch-live endpoint (202 background task) and /live-status polling
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Increase default timeout
DEFAULT_TIMEOUT = 30

class TestHealthAndSession:
    """Basic health and session tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is working"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=DEFAULT_TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("Health endpoint: PASSED")
    
    def test_create_session(self):
        """Test session creation"""
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0
        print(f"Session created: {data['session_id']}")
        return data["session_id"]
    
    def test_get_prediction_horizons(self):
        """Test prediction horizons endpoint"""
        response = requests.get(f"{BASE_URL}/api/prediction-horizons", timeout=DEFAULT_TIMEOUT)
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


class TestFetchLiveBackgroundTask:
    """Tests for fetch-live endpoint returning 202 (background task)"""
    
    @pytest.fixture
    def session_id(self):
        """Create a session for testing"""
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        assert response.status_code == 200
        return response.json()["session_id"]
    
    def test_fetch_live_returns_202(self, session_id):
        """Test that POST /fetch-live returns 202 immediately (not blocking)"""
        payload = {
            "topic": "Bitcoin price",
            "horizon": "Next week",
            "prediction_query": "What will happen to Bitcoin price next week?"
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
        elapsed = time.time() - start_time
        
        # Should return 202 immediately (within a few seconds)
        assert response.status_code == 202, f"Expected 202, got {response.status_code}"
        assert elapsed < 15, f"Response took too long: {elapsed}s (should be immediate)"
        
        data = response.json()
        assert data["status"] == "fetching"
        assert "message" in data
        print(f"Fetch-live returned 202 in {elapsed:.2f}s: PASSED")
    
    def test_fetch_live_empty_topic_returns_400(self, session_id):
        """Test that empty topic returns 400 error immediately"""
        payload = {
            "topic": "",
            "horizon": "Next week"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower() or "topic" in data["detail"].lower()
        print("Empty topic validation: PASSED")
    
    def test_fetch_live_invalid_session_returns_404(self):
        """Test fetch-live with invalid session ID returns 404"""
        payload = {
            "topic": "Test topic",
            "horizon": "Next week"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/sessions/invalid-session-id/fetch-live",
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
        
        assert response.status_code == 404
        print("Invalid session validation: PASSED")


class TestLiveStatusPolling:
    """Tests for /live-status polling endpoint"""
    
    def test_live_status_returns_progress_fields(self):
        """Test that live-status returns progress_step, progress_total, and progress message"""
        # Create session
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        session_id = response.json()["session_id"]
        
        # Start live fetch
        payload = {
            "topic": "AI regulation",
            "horizon": "Next month"
        }
        requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
        
        # Poll immediately to catch fetching status
        response = requests.get(
            f"{BASE_URL}/api/sessions/{session_id}/live-status",
            timeout=DEFAULT_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have progress fields
        assert "status" in data
        assert "progress" in data
        assert "progress_step" in data
        assert "progress_total" in data
        
        # progress_total should be 8 (8 web searches)
        assert data["progress_total"] == 8
        
        # progress_step should be between 0 and 8
        assert 0 <= data["progress_step"] <= 8
        
        print(f"Live status progress: {data['progress']} ({data['progress_step']}/{data['progress_total']})")
        print("Progress fields during fetching: PASSED")
    
    def test_live_status_invalid_session_returns_404(self):
        """Test live-status with invalid session ID returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/sessions/invalid-session-id/live-status",
            timeout=DEFAULT_TIMEOUT
        )
        
        assert response.status_code == 404
        print("Invalid session live-status: PASSED")


class TestFullLiveFetchFlow:
    """Test complete live fetch flow with polling"""
    
    def test_live_fetch_completes_with_graph_and_intel_brief(self):
        """Test that live fetch completes and returns graph and intel_brief"""
        # Create session
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        session_id = response.json()["session_id"]
        print(f"Created session: {session_id}")
        
        # Start live fetch
        payload = {
            "topic": "Tesla stock outlook",
            "horizon": "Next week"
        }
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
        assert response.status_code == 202
        print("Live fetch started (202)")
        
        # Poll until completed (max 120 seconds)
        max_polls = 60
        poll_interval = 2
        completed = False
        seen_steps = set()
        
        for i in range(max_polls):
            try:
                response = requests.get(
                    f"{BASE_URL}/api/sessions/{session_id}/live-status",
                    timeout=DEFAULT_TIMEOUT
                )
                assert response.status_code == 200
                data = response.json()
                
                # Track progress steps
                step = data.get("progress_step", 0)
                if step > 0:
                    seen_steps.add(step)
                
                if data["status"] == "completed":
                    completed = True
                    
                    # Verify completed response structure
                    assert "graph" in data, "Completed response should include graph"
                    assert "intel_brief" in data, "Completed response should include intel_brief"
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
                    
                    print(f"Completed after {i+1} polls: {len(graph['entities'])} entities, {len(graph['relationships'])} relationships")
                    print(f"Seen progress steps: {sorted(seen_steps)}")
                    print("Full live fetch flow: PASSED")
                    break
                
                elif data["status"] == "failed":
                    pytest.fail(f"Live fetch failed: {data.get('error', 'Unknown error')}")
                
                print(f"Poll {i+1}: {data['status']} - {data.get('progress', '')} ({data.get('progress_step', 0)}/{data.get('progress_total', 8)})")
                
            except requests.exceptions.Timeout:
                print(f"Poll {i+1}: Timeout, retrying...")
            
            time.sleep(poll_interval)
        
        assert completed, "Live fetch did not complete within timeout"


class TestAgentGenerationBackgroundTask:
    """Test that agent generation still works (background task + polling)"""
    
    def test_agent_generation_returns_generating_status(self):
        """Test that agent generation returns 'generating' status immediately"""
        # Create session
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        session_id = response.json()["session_id"]
        
        # Start live fetch and wait for completion
        payload = {"topic": "Bitcoin", "horizon": "Next week"}
        requests.post(f"{BASE_URL}/api/sessions/{session_id}/fetch-live", json=payload, timeout=DEFAULT_TIMEOUT)
        
        # Wait for live fetch to complete
        for i in range(60):
            response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/live-status", timeout=DEFAULT_TIMEOUT)
            if response.json().get("status") == "completed":
                break
            time.sleep(2)
        
        # Start agent generation
        agents_payload = {"num_agents": 10}
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/generate-agents",
            json=agents_payload,
            timeout=DEFAULT_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "generating"
        print("Agent generation returns 'generating' status: PASSED")


class TestDocumentUploadRegression:
    """Regression tests for Document Upload mode"""
    
    def test_upload_endpoint_exists(self):
        """Test that upload endpoint exists and requires file"""
        session_response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        session_id = session_response.json()["session_id"]
        
        # Try to call upload without file - should fail with 422
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/upload",
            data={"prediction_query": "Test question"},
            timeout=DEFAULT_TIMEOUT
        )
        
        # Should fail because no file provided
        assert response.status_code == 422
        print("Upload endpoint validation: PASSED")
    
    def test_session_default_mode_is_upload(self):
        """Test that new sessions default to upload mode"""
        session_response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        session_id = session_response.json()["session_id"]
        
        session_data = requests.get(f"{BASE_URL}/api/sessions/{session_id}", timeout=DEFAULT_TIMEOUT).json()
        assert session_data["data_mode"] == "upload"
        print("Default data_mode is 'upload': PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
