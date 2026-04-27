"""
Test suite for Predicta tiered LLM model strategy (iteration 7)
Tests: Session creation, live fetch, agent generation, simulation, report, chat
Model tiers: Premium (Sonnet 4), Fast (Haiku 4.5), Flash (Gemini 2.5 Flash)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Use existing session with completed simulation data (budget-friendly)
EXISTING_SESSION_ID = "3a2d3e92-eb87-45f5-b9ab-9c61ec67fa0f"


class TestHealthAndSession:
    """Basic health and session tests"""
    
    def test_health_check(self):
        """GET /api/health returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("✓ Health check passed")
    
    def test_create_session(self):
        """POST /api/sessions creates a new session"""
        response = requests.post(f"{BASE_URL}/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36  # UUID format
        print(f"✓ Session created: {data['session_id']}")
    
    def test_get_existing_session(self):
        """GET /api/sessions/{id} returns session data"""
        response = requests.get(f"{BASE_URL}/api/sessions/{EXISTING_SESSION_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "complete"
        assert data.get("topic") is not None
        assert data.get("agents_json") is not None
        assert data.get("graph_json") is not None
        print(f"✓ Existing session retrieved: status={data['status']}, topic={data.get('topic')}")


class TestSimulationData:
    """Tests for simulation data with required fields"""
    
    def test_simulation_status_fields(self):
        """GET /api/sessions/{id}/simulation-status returns all required fields"""
        response = requests.get(f"{BASE_URL}/api/sessions/{EXISTING_SESSION_ID}/simulation-status")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "post_count" in data
        assert "belief_summary" in data
        assert "emotional_summary" in data
        assert "network_stats" in data
        assert "round_narratives" in data
        
        # Validate values
        assert data["status"] == "complete"
        assert data["post_count"] > 0
        assert data["belief_summary"] is not None
        assert data["emotional_summary"] is not None
        assert data["network_stats"] is not None
        assert isinstance(data["round_narratives"], list)
        
        print(f"✓ Simulation status: {data['post_count']} posts, {len(data['round_narratives'])} narratives")
    
    def test_posts_have_required_fields(self):
        """GET /api/sessions/{id}/posts returns posts with is_hub_post, belief_position, emotional_valence"""
        response = requests.get(f"{BASE_URL}/api/sessions/{EXISTING_SESSION_ID}/posts")
        assert response.status_code == 200
        data = response.json()
        
        posts = data.get("posts", [])
        assert len(posts) > 0, "No posts found"
        
        # Check post types (should have both posts and replies)
        post_types = set(p.get("post_type") for p in posts)
        assert "post" in post_types, "No regular posts found"
        assert "reply" in post_types, "No replies found (batched reply generation may have failed)"
        
        # Check required fields on all posts
        for post in posts:
            assert "is_hub_post" in post, f"Missing is_hub_post in post: {post.get('agent_name')}"
            assert "belief_position" in post, f"Missing belief_position in post: {post.get('agent_name')}"
            assert "emotional_valence" in post, f"Missing emotional_valence in post: {post.get('agent_name')}"
        
        # Count post types
        post_count = sum(1 for p in posts if p.get("post_type") == "post")
        reply_count = sum(1 for p in posts if p.get("post_type") == "reply")
        
        print(f"✓ Posts verified: {post_count} posts, {reply_count} replies, all have required fields")


class TestReportGeneration:
    """Tests for report generation with quality score and factions"""
    
    def test_get_report_fields(self):
        """GET /api/sessions/{id}/report returns report with quality_score, factions, prediction"""
        response = requests.get(f"{BASE_URL}/api/sessions/{EXISTING_SESSION_ID}/report")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "quality_score" in data, "Missing quality_score"
        assert "prediction" in data, "Missing prediction"
        
        # Validate quality score
        quality_score = data.get("quality_score")
        assert isinstance(quality_score, (int, float)), "quality_score should be numeric"
        assert 0 <= quality_score <= 10, f"quality_score {quality_score} out of range [0,10]"
        
        # Validate prediction
        prediction = data.get("prediction", {})
        assert "outcome" in prediction, "Missing prediction outcome"
        assert "confidence" in prediction, "Missing prediction confidence"
        
        print(f"✓ Report verified: quality_score={quality_score}, confidence={prediction.get('confidence')}")
    
    def test_generate_report_endpoint(self):
        """POST /api/sessions/{id}/generate-report works (may return existing report)"""
        response = requests.post(f"{BASE_URL}/api/sessions/{EXISTING_SESSION_ID}/generate-report")
        assert response.status_code == 200
        data = response.json()
        
        assert "report" in data
        report = data["report"]
        assert "quality_score" in report
        assert "prediction" in report
        
        print(f"✓ Generate report endpoint works: quality_score={report.get('quality_score')}")


class TestChatEndpoint:
    """Tests for chat with agent"""
    
    def test_chat_with_agent(self):
        """POST /api/sessions/{id}/chat works with agent"""
        response = requests.post(
            f"{BASE_URL}/api/sessions/{EXISTING_SESSION_ID}/chat",
            json={
                "target_type": "agent",
                "target_id": "agent_1",
                "message": "What is your view on the topic?"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data, "Missing response in chat"
        assert len(data["response"]) > 10, "Response too short"
        
        print(f"✓ Chat works: response length={len(data['response'])} chars")


class TestLiveFetchFlow:
    """Tests for live intelligence fetch flow (creates new session)"""
    
    def test_fetch_live_returns_202(self):
        """POST /api/sessions/{id}/fetch-live returns 202 and starts background task"""
        # Create new session
        create_resp = requests.post(f"{BASE_URL}/api/sessions")
        assert create_resp.status_code == 200
        session_id = create_resp.json()["session_id"]
        
        # Start live fetch
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json={
                "topic": "AI regulation outlook",
                "horizon": "Next month",
                "prediction_query": "What will happen with AI regulation?"
            }
        )
        assert response.status_code == 202
        data = response.json()
        assert data.get("status") == "fetching"
        
        print(f"✓ Live fetch started for session {session_id}")
        
        # Poll for completion (max 90 seconds)
        max_wait = 90
        start_time = time.time()
        completed = False
        
        while time.time() - start_time < max_wait:
            status_resp = requests.get(f"{BASE_URL}/api/sessions/{session_id}/live-status")
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                status = status_data.get("status")
                progress = status_data.get("progress", "")
                
                if status == "completed":
                    completed = True
                    graph = status_data.get("graph", {})
                    entities = graph.get("entities", [])
                    print(f"✓ Live fetch completed: {len(entities)} entities extracted")
                    assert len(entities) > 0, "No entities extracted"
                    break
                elif status == "failed":
                    error = status_data.get("error", "Unknown error")
                    pytest.fail(f"Live fetch failed: {error}")
                else:
                    print(f"  Progress: {progress}")
            
            time.sleep(5)
        
        assert completed, f"Live fetch did not complete within {max_wait} seconds"


class TestAgentGeneration:
    """Tests for agent generation flow"""
    
    def test_agent_status_returns_agents(self):
        """GET /api/sessions/{id}/agent-status returns completed agents"""
        response = requests.get(f"{BASE_URL}/api/sessions/{EXISTING_SESSION_ID}/agent-status")
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("status") == "completed"
        assert "agents" in data
        assert "count" in data
        assert data["count"] > 0
        
        # Verify agent structure
        agents = data["agents"]
        sample_agent = agents[0]
        required_fields = ["id", "name", "occupation", "personality_type", "initial_stance"]
        for field in required_fields:
            assert field in sample_agent, f"Missing field {field} in agent"
        
        print(f"✓ Agent status: {data['count']} agents with all required fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
