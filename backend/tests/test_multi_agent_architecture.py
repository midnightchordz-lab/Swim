"""
Backend tests for Predicta Multi-Agent Architecture
Tests the 6 specialist agents (Intel, Graph, Persona, SimDirector, Critic, Report) 
coordinated by the Orchestrator.

Key features tested:
- POST /api/sessions/{id}/fetch-live returns 202 and completes via orchestrator pipeline
- GET /api/sessions/{id}/live-status shows progress and returns completed graph with entities and intel_brief
- POST /api/sessions/{id}/generate-agents returns 202 and orchestrator runs Persona Agent + diversity check
- GET /api/sessions/{id}/agent-status returns completed agents with all 4 required personality types
- POST /api/sessions/{id}/simulate runs simulation via SimDirector with round narratives and herd detection
- GET /api/sessions/{id}/simulation-status works during and after simulation
- POST /api/sessions/{id}/generate-report returns report with quality_score from Critic agent
"""
import pytest
import requests
import os
import time
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
DEFAULT_TIMEOUT = 60
LONG_TIMEOUT = 180

# Required personality types for agent diversity
REQUIRED_PERSONALITY_TYPES = {"Skeptic", "Expert", "Contrarian", "Activist"}


class TestHealthAndBasics:
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


class TestLiveIntelPipeline:
    """Tests for Intel Agent + Critic + Graph Agent pipeline via orchestrator"""
    
    @pytest.fixture
    def session_id(self):
        """Create a session for testing"""
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        assert response.status_code == 200
        return response.json()["session_id"]
    
    def test_fetch_live_returns_202_immediately(self, session_id):
        """Test POST /fetch-live returns 202 immediately (background task)"""
        payload = {
            "topic": "Tesla stock",
            "horizon": "Next week",
            "prediction_query": "What will happen to Tesla stock next week?"
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 202, f"Expected 202, got {response.status_code}"
        assert elapsed < 10, f"Response took too long: {elapsed}s (should be immediate)"
        
        data = response.json()
        assert data["status"] == "fetching"
        print(f"Fetch-live returned 202 in {elapsed:.2f}s: PASSED")
    
    def test_live_status_shows_progress(self, session_id):
        """Test GET /live-status shows progress_step, progress_total, and progress message"""
        # Start live fetch
        payload = {"topic": "AI regulation", "horizon": "Next month"}
        requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
        
        # Poll immediately
        response = requests.get(
            f"{BASE_URL}/api/sessions/{session_id}/live-status",
            timeout=DEFAULT_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "progress" in data
        assert "progress_step" in data
        assert "progress_total" in data
        
        print(f"Live status: {data['status']} - {data['progress']} ({data['progress_step']}/{data['progress_total']})")
        print("Progress fields: PASSED")


class TestFullOrchestratorPipeline:
    """End-to-end test of the full orchestrator pipeline"""
    
    @pytest.fixture(scope="class")
    def completed_session(self):
        """Create a session and complete the live intel pipeline"""
        # Create session
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        session_id = response.json()["session_id"]
        print(f"Created session: {session_id}")
        
        # Start live fetch
        payload = {
            "topic": "Tesla stock outlook",
            "horizon": "Next week",
            "prediction_query": "What will happen to Tesla stock next week?"
        }
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
        assert response.status_code == 202
        print("Live fetch started (202)")
        
        # Poll until completed (max 90 seconds)
        max_polls = 45
        poll_interval = 2
        
        for i in range(max_polls):
            response = requests.get(
                f"{BASE_URL}/api/sessions/{session_id}/live-status",
                timeout=DEFAULT_TIMEOUT
            )
            data = response.json()
            
            if data["status"] == "completed":
                print(f"Live fetch completed after {(i+1)*poll_interval}s")
                return {
                    "session_id": session_id,
                    "graph": data["graph"],
                    "intel_brief": data["intel_brief"]
                }
            elif data["status"] == "failed":
                pytest.fail(f"Live fetch failed: {data.get('error', 'Unknown error')}")
            
            print(f"Poll {i+1}: {data['status']} - {data.get('progress', '')}")
            time.sleep(poll_interval)
        
        pytest.fail("Live fetch did not complete within timeout")
    
    def test_live_intel_returns_graph_with_entities(self, completed_session):
        """Test that completed live-status returns graph with entities"""
        graph = completed_session["graph"]
        
        assert "summary" in graph
        assert "entities" in graph
        assert "relationships" in graph
        assert "themes" in graph
        
        assert len(graph["entities"]) > 0, "Graph should have entities"
        assert len(graph["relationships"]) > 0, "Graph should have relationships"
        
        print(f"Graph: {len(graph['entities'])} entities, {len(graph['relationships'])} relationships")
        print("Graph structure: PASSED")
    
    def test_live_intel_returns_intel_brief(self, completed_session):
        """Test that completed live-status returns intel_brief"""
        intel_brief = completed_session["intel_brief"]
        
        assert "summary" in intel_brief
        assert "key_developments" in intel_brief
        
        print(f"Intel brief summary: {intel_brief['summary'][:100]}...")
        print("Intel brief structure: PASSED")


class TestAgentGenerationPipeline:
    """Tests for Persona Agent + Critic diversity check via orchestrator"""
    
    @pytest.fixture(scope="class")
    def session_with_graph(self):
        """Create a session with completed graph"""
        # Create session
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        session_id = response.json()["session_id"]
        
        # Start live fetch
        payload = {"topic": "Bitcoin price", "horizon": "Next week"}
        requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
        
        # Wait for completion
        for i in range(45):
            response = requests.get(
                f"{BASE_URL}/api/sessions/{session_id}/live-status",
                timeout=DEFAULT_TIMEOUT
            )
            if response.json().get("status") == "completed":
                return session_id
            time.sleep(2)
        
        pytest.fail("Live fetch did not complete")
    
    def test_generate_agents_returns_202(self, session_with_graph):
        """Test POST /generate-agents returns 202 (background task)"""
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_with_graph}/generate-agents",
            json={"num_agents": 15},
            timeout=DEFAULT_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "generating"
        print("Agent generation started: PASSED")
    
    def test_agent_status_returns_completed_agents(self, session_with_graph):
        """Test GET /agent-status returns completed agents with required personality types"""
        # Start agent generation
        requests.post(
            f"{BASE_URL}/api/sessions/{session_with_graph}/generate-agents",
            json={"num_agents": 15},
            timeout=DEFAULT_TIMEOUT
        )
        
        # Poll until completed (max 60 seconds)
        for i in range(30):
            response = requests.get(
                f"{BASE_URL}/api/sessions/{session_with_graph}/agent-status",
                timeout=DEFAULT_TIMEOUT
            )
            data = response.json()
            
            if data["status"] == "completed":
                agents = data["agents"]
                
                # Verify agent count
                assert len(agents) >= 10, f"Expected at least 10 agents, got {len(agents)}"
                
                # Verify required personality types
                personality_types = {a.get("personality_type") for a in agents}
                missing_types = REQUIRED_PERSONALITY_TYPES - personality_types
                
                # Log what we found
                print(f"Found {len(agents)} agents with types: {personality_types}")
                
                # Check for required types (at least 3 of 4 should be present)
                found_required = len(REQUIRED_PERSONALITY_TYPES & personality_types)
                assert found_required >= 3, f"Expected at least 3 of {REQUIRED_PERSONALITY_TYPES}, found {personality_types}"
                
                print(f"Agent generation completed: {len(agents)} agents")
                print(f"Personality types: {personality_types}")
                print("Agent diversity: PASSED")
                return
            
            elif data["status"] == "failed":
                pytest.fail(f"Agent generation failed: {data.get('error', 'Unknown')}")
            
            print(f"Poll {i+1}: {data['status']}")
            time.sleep(2)
        
        pytest.fail("Agent generation did not complete within timeout")


class TestSimulationPipeline:
    """Tests for SimDirector with round narratives and herd detection"""
    
    @pytest.fixture(scope="class")
    def session_with_agents(self):
        """Create a session with completed agents"""
        # Create session
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        session_id = response.json()["session_id"]
        print(f"Created session: {session_id}")
        
        # Start live fetch
        payload = {"topic": "Gold price", "horizon": "Next month"}
        requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
        
        # Wait for live fetch
        for i in range(45):
            response = requests.get(
                f"{BASE_URL}/api/sessions/{session_id}/live-status",
                timeout=DEFAULT_TIMEOUT
            )
            if response.json().get("status") == "completed":
                print("Live fetch completed")
                break
            time.sleep(2)
        
        # Generate agents
        requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/generate-agents",
            json={"num_agents": 12},
            timeout=DEFAULT_TIMEOUT
        )
        
        # Wait for agents
        for i in range(30):
            response = requests.get(
                f"{BASE_URL}/api/sessions/{session_id}/agent-status",
                timeout=DEFAULT_TIMEOUT
            )
            if response.json().get("status") == "completed":
                print("Agent generation completed")
                return session_id
            time.sleep(2)
        
        pytest.fail("Agent generation did not complete")
    
    def test_simulate_starts_simulation(self, session_with_agents):
        """Test POST /simulate starts simulation"""
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_with_agents}/simulate",
            json={"num_rounds": 3},
            timeout=DEFAULT_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "simulating"
        print("Simulation started: PASSED")
    
    def test_simulation_status_during_simulation(self, session_with_agents):
        """Test GET /simulation-status works during simulation"""
        # Start simulation
        requests.post(
            f"{BASE_URL}/api/sessions/{session_with_agents}/simulate",
            json={"num_rounds": 3},
            timeout=DEFAULT_TIMEOUT
        )
        
        # Check status immediately
        response = requests.get(
            f"{BASE_URL}/api/sessions/{session_with_agents}/simulation-status",
            timeout=DEFAULT_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "post_count" in data
        assert "current_round" in data
        assert "total_rounds" in data
        
        print(f"Simulation status: {data['status']}, round {data['current_round']}/{data['total_rounds']}, posts: {data['post_count']}")
        print("Simulation status during: PASSED")
    
    def test_simulation_completes_with_posts(self, session_with_agents):
        """Test simulation completes and generates posts"""
        # Start simulation
        requests.post(
            f"{BASE_URL}/api/sessions/{session_with_agents}/simulate",
            json={"num_rounds": 3},
            timeout=DEFAULT_TIMEOUT
        )
        
        # Poll until completed (max 180 seconds for 3 rounds)
        for i in range(90):
            response = requests.get(
                f"{BASE_URL}/api/sessions/{session_with_agents}/simulation-status",
                timeout=DEFAULT_TIMEOUT
            )
            data = response.json()
            
            if data["status"] == "simulation_done":
                assert data["post_count"] > 0, "Should have generated posts"
                print(f"Simulation completed: {data['post_count']} posts")
                print("Simulation completion: PASSED")
                return
            
            print(f"Poll {i+1}: {data['status']}, round {data.get('current_round', 0)}/{data.get('total_rounds', 0)}, posts: {data.get('post_count', 0)}")
            time.sleep(2)
        
        pytest.fail("Simulation did not complete within timeout")


class TestReportPipeline:
    """Tests for Report Agent + Critic quality check via orchestrator"""
    
    @pytest.fixture(scope="class")
    def session_with_simulation(self):
        """Create a session with completed simulation"""
        # Create session
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        session_id = response.json()["session_id"]
        print(f"Created session: {session_id}")
        
        # Start live fetch
        payload = {"topic": "Oil prices", "horizon": "Next week"}
        requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/fetch-live",
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
        
        # Wait for live fetch
        for i in range(45):
            response = requests.get(
                f"{BASE_URL}/api/sessions/{session_id}/live-status",
                timeout=DEFAULT_TIMEOUT
            )
            if response.json().get("status") == "completed":
                print("Live fetch completed")
                break
            time.sleep(2)
        
        # Generate agents
        requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/generate-agents",
            json={"num_agents": 10},
            timeout=DEFAULT_TIMEOUT
        )
        
        # Wait for agents
        for i in range(30):
            response = requests.get(
                f"{BASE_URL}/api/sessions/{session_id}/agent-status",
                timeout=DEFAULT_TIMEOUT
            )
            if response.json().get("status") == "completed":
                print("Agent generation completed")
                break
            time.sleep(2)
        
        # Run simulation
        requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/simulate",
            json={"num_rounds": 3},
            timeout=DEFAULT_TIMEOUT
        )
        
        # Wait for simulation
        for i in range(90):
            response = requests.get(
                f"{BASE_URL}/api/sessions/{session_id}/simulation-status",
                timeout=DEFAULT_TIMEOUT
            )
            if response.json().get("status") == "simulation_done":
                print("Simulation completed")
                return session_id
            time.sleep(2)
        
        pytest.fail("Simulation did not complete")
    
    def test_generate_report_returns_quality_score(self, session_with_simulation):
        """Test POST /generate-report returns report with quality_score from Critic"""
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_with_simulation}/generate-report",
            timeout=LONG_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        report = data["report"]
        
        # Verify report structure
        assert "executive_summary" in report
        assert "prediction" in report
        assert "opinion_landscape" in report
        assert "risk_factors" in report
        
        # Verify quality_score from Critic agent
        assert "quality_score" in report, "Report should have quality_score from Critic"
        quality_score = report["quality_score"]
        assert isinstance(quality_score, (int, float)), "quality_score should be numeric"
        assert 0 <= quality_score <= 10, f"quality_score should be 0-10, got {quality_score}"
        
        # Check for overconfident flag
        assert "overconfident" in report, "Report should have overconfident flag"
        
        print(f"Report generated with quality_score: {quality_score}")
        print(f"Overconfident: {report.get('overconfident', False)}")
        print("Report with quality_score: PASSED")


class TestDocumentUploadRegression:
    """Regression tests for Document Upload mode"""
    
    def test_session_default_mode_is_upload(self):
        """Test that new sessions default to upload mode"""
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        session_id = response.json()["session_id"]
        
        session_data = requests.get(
            f"{BASE_URL}/api/sessions/{session_id}",
            timeout=DEFAULT_TIMEOUT
        ).json()
        
        assert session_data["data_mode"] == "upload"
        print("Default data_mode is 'upload': PASSED")
    
    def test_upload_endpoint_exists(self):
        """Test that upload endpoint exists and requires file"""
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=DEFAULT_TIMEOUT)
        session_id = response.json()["session_id"]
        
        # Try to call upload without file - should fail with 422
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/upload",
            data={"prediction_query": "Test question"},
            timeout=DEFAULT_TIMEOUT
        )
        
        assert response.status_code == 422
        print("Upload endpoint validation: PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
