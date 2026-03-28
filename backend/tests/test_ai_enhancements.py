"""
Test suite for SwarmSim AI Enhancements:
- Belief tracking (initialise_beliefs, update_beliefs, get_belief_summary)
- Emotional contagion (initialise_emotions, spread_emotions, get_emotional_temperature)
- Network effects (assign_network_properties, get_network_stats)
- Critic agent (check_herd, score_diversity, check_report)
- Simulation posts with new fields (is_hub_post, belief_position, emotional_valence)
- Report quality scoring (quality_score, quality_feedback, overconfident, quality_issues)
"""

import pytest
import requests
import os
import time
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndSetup:
    """Basic health checks"""
    
    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✓ Health endpoint working")


class TestAgentSliderMax:
    """Test that agent slider max is now 300"""
    
    def test_generate_agents_accepts_300(self):
        """Agent generation should accept up to 300 agents"""
        # Create session first
        session_res = requests.post(f"{BASE_URL}/api/sessions")
        assert session_res.status_code == 200
        session_id = session_res.json()["session_id"]
        print(f"✓ Created session: {session_id[:8]}")
        
        # We need a graph first - use live fetch with a quick topic
        fetch_res = requests.post(f"{BASE_URL}/api/sessions/{session_id}/fetch-live", json={
            "topic": "Bitcoin price",
            "horizon": "Next week",
            "prediction_query": "Will Bitcoin go up?"
        })
        assert fetch_res.status_code == 202
        print("✓ Live fetch started")
        
        # Poll for completion (max 90 seconds)
        for _ in range(45):
            status_res = requests.get(f"{BASE_URL}/api/sessions/{session_id}/live-status")
            if status_res.json().get("status") == "completed":
                break
            time.sleep(2)
        
        status_data = status_res.json()
        assert status_data.get("status") == "completed", f"Live fetch did not complete: {status_data}"
        print("✓ Live fetch completed")
        
        # Now test that we can request 300 agents (just validate the request is accepted)
        # We won't wait for completion since it would take too long
        gen_res = requests.post(f"{BASE_URL}/api/sessions/{session_id}/generate-agents", json={
            "num_agents": 300
        })
        # Should accept the request (either 200 or 202)
        assert gen_res.status_code in [200, 202], f"Failed to accept 300 agents: {gen_res.text}"
        print("✓ Agent generation accepts 300 agents (max slider value)")


class TestLiveFetchWithGraph:
    """Test POST /api/sessions/{id}/fetch-live returns 202 and completes with graph"""
    
    def test_fetch_live_returns_202_and_completes(self):
        # Create session
        session_res = requests.post(f"{BASE_URL}/api/sessions")
        assert session_res.status_code == 200
        session_id = session_res.json()["session_id"]
        print(f"✓ Created session: {session_id[:8]}")
        
        # Start live fetch
        fetch_res = requests.post(f"{BASE_URL}/api/sessions/{session_id}/fetch-live", json={
            "topic": "Tesla stock",
            "horizon": "Next month",
            "prediction_query": "Will Tesla stock rise?"
        })
        assert fetch_res.status_code == 202, f"Expected 202, got {fetch_res.status_code}"
        print("✓ Live fetch returns 202 (background task started)")
        
        # Poll for completion
        completed = False
        for _ in range(60):
            status_res = requests.get(f"{BASE_URL}/api/sessions/{session_id}/live-status")
            status_data = status_res.json()
            if status_data.get("status") == "completed":
                completed = True
                # Verify graph is present
                assert "graph" in status_data, "Graph not in completed response"
                assert status_data["graph"] is not None, "Graph is None"
                assert "entities" in status_data["graph"], "No entities in graph"
                assert len(status_data["graph"]["entities"]) > 0, "Empty entities list"
                print(f"✓ Live fetch completed with {len(status_data['graph']['entities'])} entities")
                break
            time.sleep(2)
        
        assert completed, "Live fetch did not complete within timeout"


class TestAgentGeneration:
    """Test POST /api/sessions/{id}/generate-agents completes with agents"""
    
    @pytest.fixture
    def session_with_graph(self):
        """Create a session with completed graph"""
        session_res = requests.post(f"{BASE_URL}/api/sessions")
        session_id = session_res.json()["session_id"]
        
        # Fetch live data
        requests.post(f"{BASE_URL}/api/sessions/{session_id}/fetch-live", json={
            "topic": "AI regulation",
            "horizon": "Next 3 months"
        })
        
        # Wait for completion
        for _ in range(60):
            status_res = requests.get(f"{BASE_URL}/api/sessions/{session_id}/live-status")
            if status_res.json().get("status") == "completed":
                break
            time.sleep(2)
        
        return session_id
    
    def test_generate_agents_completes(self, session_with_graph):
        session_id = session_with_graph
        
        # Start agent generation with 15 agents (faster)
        gen_res = requests.post(f"{BASE_URL}/api/sessions/{session_id}/generate-agents", json={
            "num_agents": 15
        })
        assert gen_res.status_code in [200, 202]
        print("✓ Agent generation started")
        
        # Poll for completion
        completed = False
        for _ in range(60):
            status_res = requests.get(f"{BASE_URL}/api/sessions/{session_id}/agent-status")
            status_data = status_res.json()
            if status_data.get("status") == "completed":
                completed = True
                assert "agents" in status_data, "No agents in response"
                assert len(status_data["agents"]) > 0, "Empty agents list"
                print(f"✓ Agent generation completed with {len(status_data['agents'])} agents")
                break
            time.sleep(2)
        
        assert completed, "Agent generation did not complete within timeout"


class TestSimulationWithAIEnhancements:
    """Test simulation with new AI enhancement fields"""
    
    @pytest.fixture
    def session_ready_for_simulation(self):
        """Create a session ready for simulation"""
        session_res = requests.post(f"{BASE_URL}/api/sessions")
        session_id = session_res.json()["session_id"]
        
        # Fetch live data
        requests.post(f"{BASE_URL}/api/sessions/{session_id}/fetch-live", json={
            "topic": "Federal Reserve interest rates",
            "horizon": "Next month"
        })
        
        for _ in range(60):
            status_res = requests.get(f"{BASE_URL}/api/sessions/{session_id}/live-status")
            if status_res.json().get("status") == "completed":
                break
            time.sleep(2)
        
        # Generate agents
        requests.post(f"{BASE_URL}/api/sessions/{session_id}/generate-agents", json={
            "num_agents": 12
        })
        
        for _ in range(60):
            status_res = requests.get(f"{BASE_URL}/api/sessions/{session_id}/agent-status")
            if status_res.json().get("status") == "completed":
                break
            time.sleep(2)
        
        return session_id
    
    def test_simulation_starts_successfully(self, session_ready_for_simulation):
        session_id = session_ready_for_simulation
        
        # Start simulation with 3 rounds (minimum)
        sim_res = requests.post(f"{BASE_URL}/api/sessions/{session_id}/simulate", json={
            "num_rounds": 3
        })
        assert sim_res.status_code == 200, f"Failed to start simulation: {sim_res.text}"
        assert sim_res.json().get("status") == "simulating"
        print("✓ Simulation started successfully")
    
    def test_simulation_status_returns_new_fields(self, session_ready_for_simulation):
        session_id = session_ready_for_simulation
        
        # Start simulation
        requests.post(f"{BASE_URL}/api/sessions/{session_id}/simulate", json={
            "num_rounds": 3
        })
        
        # Wait for simulation to complete
        completed = False
        for _ in range(90):
            status_res = requests.get(f"{BASE_URL}/api/sessions/{session_id}/simulation-status")
            status_data = status_res.json()
            
            if status_data.get("status") == "simulation_done":
                completed = True
                # Verify new AI enhancement fields
                assert "belief_summary" in status_data, "belief_summary not in response"
                assert "emotional_summary" in status_data, "emotional_summary not in response"
                assert "network_stats" in status_data, "network_stats not in response"
                assert "round_narratives" in status_data, "round_narratives not in response"
                
                # Verify belief_summary structure
                belief = status_data["belief_summary"]
                if belief:
                    assert "support" in belief, "support not in belief_summary"
                    assert "opposition" in belief, "opposition not in belief_summary"
                    assert "undecided" in belief, "undecided not in belief_summary"
                    print(f"✓ belief_summary: support={belief['support']}%, opposition={belief['opposition']}%, undecided={belief['undecided']}%")
                
                # Verify emotional_summary structure
                emotional = status_data["emotional_summary"]
                if emotional:
                    assert "state" in emotional, "state not in emotional_summary"
                    assert "mean_valence" in emotional, "mean_valence not in emotional_summary"
                    assert "mean_arousal" in emotional, "mean_arousal not in emotional_summary"
                    print(f"✓ emotional_summary: state={emotional['state']}, valence={emotional['mean_valence']}")
                
                # Verify network_stats structure
                network = status_data["network_stats"]
                if network:
                    assert "hub_count" in network, "hub_count not in network_stats"
                    assert "total_agents" in network, "total_agents not in network_stats"
                    print(f"✓ network_stats: {network['hub_count']} hubs out of {network['total_agents']} agents")
                
                # Verify round_narratives
                narratives = status_data["round_narratives"]
                if narratives:
                    assert isinstance(narratives, list), "round_narratives should be a list"
                    print(f"✓ round_narratives: {len(narratives)} narratives")
                
                break
            time.sleep(2)
        
        assert completed, "Simulation did not complete within timeout"
    
    def test_simulation_posts_have_new_fields(self, session_ready_for_simulation):
        session_id = session_ready_for_simulation
        
        # Start simulation
        requests.post(f"{BASE_URL}/api/sessions/{session_id}/simulate", json={
            "num_rounds": 3
        })
        
        # Wait for simulation to complete
        for _ in range(90):
            status_res = requests.get(f"{BASE_URL}/api/sessions/{session_id}/simulation-status")
            if status_res.json().get("status") == "simulation_done":
                break
            time.sleep(2)
        
        # Get posts
        posts_res = requests.get(f"{BASE_URL}/api/sessions/{session_id}/posts")
        assert posts_res.status_code == 200
        posts = posts_res.json().get("posts", [])
        assert len(posts) > 0, "No posts generated"
        
        # Check that posts have new fields
        hub_posts_found = False
        for post in posts:
            # Verify is_hub_post field exists
            assert "is_hub_post" in post, f"is_hub_post not in post: {post.get('agent_name')}"
            if post["is_hub_post"]:
                hub_posts_found = True
            
            # Verify belief_position field exists
            assert "belief_position" in post, f"belief_position not in post: {post.get('agent_name')}"
            assert isinstance(post["belief_position"], (int, float)), "belief_position should be numeric"
            
            # Verify emotional_valence field exists
            assert "emotional_valence" in post, f"emotional_valence not in post: {post.get('agent_name')}"
            assert isinstance(post["emotional_valence"], (int, float)), "emotional_valence should be numeric"
        
        print(f"✓ All {len(posts)} posts have is_hub_post, belief_position, emotional_valence fields")
        if hub_posts_found:
            print("✓ Found hub posts (is_hub_post=True)")


class TestReportWithQualityScoring:
    """Test POST /api/sessions/{id}/generate-report returns report with quality fields"""
    
    @pytest.fixture
    def session_with_completed_simulation(self):
        """Create a session with completed simulation"""
        session_res = requests.post(f"{BASE_URL}/api/sessions")
        session_id = session_res.json()["session_id"]
        
        # Fetch live data
        requests.post(f"{BASE_URL}/api/sessions/{session_id}/fetch-live", json={
            "topic": "Gold price outlook",
            "horizon": "Next week"
        })
        
        for _ in range(60):
            status_res = requests.get(f"{BASE_URL}/api/sessions/{session_id}/live-status")
            if status_res.json().get("status") == "completed":
                break
            time.sleep(2)
        
        # Generate agents
        requests.post(f"{BASE_URL}/api/sessions/{session_id}/generate-agents", json={
            "num_agents": 10
        })
        
        for _ in range(60):
            status_res = requests.get(f"{BASE_URL}/api/sessions/{session_id}/agent-status")
            if status_res.json().get("status") == "completed":
                break
            time.sleep(2)
        
        # Run simulation
        requests.post(f"{BASE_URL}/api/sessions/{session_id}/simulate", json={
            "num_rounds": 3
        })
        
        for _ in range(90):
            status_res = requests.get(f"{BASE_URL}/api/sessions/{session_id}/simulation-status")
            if status_res.json().get("status") == "simulation_done":
                break
            time.sleep(2)
        
        return session_id
    
    def test_report_has_quality_fields(self, session_with_completed_simulation):
        session_id = session_with_completed_simulation
        
        # Generate report
        report_res = requests.post(f"{BASE_URL}/api/sessions/{session_id}/generate-report")
        assert report_res.status_code == 200, f"Failed to generate report: {report_res.text}"
        
        report = report_res.json().get("report", {})
        
        # Verify quality_score
        assert "quality_score" in report, "quality_score not in report"
        assert isinstance(report["quality_score"], (int, float)), "quality_score should be numeric"
        assert 1 <= report["quality_score"] <= 10, f"quality_score should be 1-10, got {report['quality_score']}"
        print(f"✓ quality_score: {report['quality_score']}/10")
        
        # Verify quality_feedback
        assert "quality_feedback" in report, "quality_feedback not in report"
        print(f"✓ quality_feedback: {report['quality_feedback']}")
        
        # Verify overconfident
        assert "overconfident" in report, "overconfident not in report"
        assert isinstance(report["overconfident"], bool), "overconfident should be boolean"
        print(f"✓ overconfident: {report['overconfident']}")
        
        # Verify quality_issues
        assert "quality_issues" in report, "quality_issues not in report"
        assert isinstance(report["quality_issues"], list), "quality_issues should be a list"
        print(f"✓ quality_issues: {len(report['quality_issues'])} issues")


class TestBeliefTrackerModule:
    """Unit tests for belief_tracker module functions"""
    
    def test_initialise_beliefs(self):
        """Test that initialise_beliefs adds belief_state to agents"""
        from agents.belief_tracker import initialise_beliefs
        
        agents = [
            {"id": "1", "initial_stance": "I am bullish on this", "influence_level": 8},
            {"id": "2", "initial_stance": "I am bearish and worried", "influence_level": 3},
            {"id": "3", "initial_stance": "Neutral stance", "influence_level": 5},
        ]
        
        result = initialise_beliefs(agents)
        
        for agent in result:
            assert "belief_state" in agent, f"belief_state not added to agent {agent['id']}"
            bs = agent["belief_state"]
            assert "position" in bs, "position not in belief_state"
            assert "certainty" in bs, "certainty not in belief_state"
            assert "prior" in bs, "prior not in belief_state"
            assert "history" in bs, "history not in belief_state"
            assert -1.0 <= bs["position"] <= 1.0, f"position out of range: {bs['position']}"
        
        print("✓ initialise_beliefs adds belief_state to all agents")
    
    def test_get_belief_summary(self):
        """Test that get_belief_summary returns correct structure"""
        from agents.belief_tracker import get_belief_summary
        
        agents = [
            {"belief_state": {"position": 0.5}},  # support
            {"belief_state": {"position": 0.3}},  # support
            {"belief_state": {"position": -0.5}},  # opposition
            {"belief_state": {"position": 0.0}},  # undecided
        ]
        
        summary = get_belief_summary(agents)
        
        assert "support" in summary, "support not in summary"
        assert "opposition" in summary, "opposition not in summary"
        assert "undecided" in summary, "undecided not in summary"
        assert summary["support"] + summary["opposition"] + summary["undecided"] == 100, "Percentages don't sum to 100"
        
        print(f"✓ get_belief_summary: support={summary['support']}%, opposition={summary['opposition']}%, undecided={summary['undecided']}%")


class TestEmotionalContagionModule:
    """Unit tests for emotional_contagion module functions"""
    
    def test_initialise_emotions(self):
        """Test that initialise_emotions adds emotional_state to agents"""
        from agents.emotional_contagion import initialise_emotions
        
        agents = [
            {"id": "1", "personality_type": "Skeptic"},
            {"id": "2", "personality_type": "Optimist"},
            {"id": "3", "personality_type": "Activist"},
        ]
        
        result = initialise_emotions(agents)
        
        for agent in result:
            assert "emotional_state" in agent, f"emotional_state not added to agent {agent['id']}"
            es = agent["emotional_state"]
            assert "valence" in es, "valence not in emotional_state"
            assert "arousal" in es, "arousal not in emotional_state"
            assert "susceptibility" in es, "susceptibility not in emotional_state"
            assert "history" in es, "history not in emotional_state"
        
        print("✓ initialise_emotions adds emotional_state to all agents")
    
    def test_get_emotional_temperature(self):
        """Test that get_emotional_temperature returns correct structure"""
        from agents.emotional_contagion import get_emotional_temperature
        
        agents = [
            {"emotional_state": {"valence": 0.6, "arousal": 0.7}},
            {"emotional_state": {"valence": 0.4, "arousal": 0.5}},
            {"emotional_state": {"valence": 0.5, "arousal": 0.6}},
        ]
        
        temp = get_emotional_temperature(agents)
        
        assert "mean_valence" in temp, "mean_valence not in temperature"
        assert "mean_arousal" in temp, "mean_arousal not in temperature"
        assert "state" in temp, "state not in temperature"
        assert temp["state"] in ["PANIC", "fear", "agitated", "calm", "optimism", "EUPHORIA"], f"Unknown state: {temp['state']}"
        
        print(f"✓ get_emotional_temperature: state={temp['state']}, valence={temp['mean_valence']}, arousal={temp['mean_arousal']}")


class TestNetworkModule:
    """Unit tests for network module functions"""
    
    def test_assign_network_properties(self):
        """Test that assign_network_properties adds network fields to agents"""
        from agents.network import assign_network_properties
        
        agents = [{"id": str(i)} for i in range(20)]
        
        result = assign_network_properties(agents)
        
        hub_count = 0
        for agent in result:
            assert "follower_count" in agent, f"follower_count not added to agent {agent['id']}"
            assert "is_hub" in agent, f"is_hub not added to agent {agent['id']}"
            assert "network_tier" in agent, f"network_tier not added to agent {agent['id']}"
            assert "following" in agent, f"following not added to agent {agent['id']}"
            assert agent["network_tier"] in ["hub", "peripheral"], f"Unknown tier: {agent['network_tier']}"
            if agent["is_hub"]:
                hub_count += 1
        
        # Should have ~10% hubs (2 out of 20)
        assert hub_count > 0, "No hubs assigned"
        print(f"✓ assign_network_properties: {hub_count} hubs out of {len(agents)} agents")
    
    def test_get_network_stats(self):
        """Test that get_network_stats returns correct structure"""
        from agents.network import get_network_stats, assign_network_properties
        
        agents = [{"id": str(i)} for i in range(15)]
        agents = assign_network_properties(agents)
        
        stats = get_network_stats(agents)
        
        assert "total_agents" in stats, "total_agents not in stats"
        assert "hub_count" in stats, "hub_count not in stats"
        assert "peripheral_count" in stats, "peripheral_count not in stats"
        assert "hub_ids" in stats, "hub_ids not in stats"
        assert stats["total_agents"] == 15, f"Expected 15 agents, got {stats['total_agents']}"
        assert stats["hub_count"] + stats["peripheral_count"] == stats["total_agents"], "Hub + peripheral != total"
        
        print(f"✓ get_network_stats: {stats['hub_count']} hubs, {stats['peripheral_count']} peripherals")


class TestCriticModule:
    """Unit tests for critic module functions"""
    
    def test_check_herd(self):
        """Test that check_herd detects herd behavior"""
        from agents.critic import check_herd
        
        # Create posts with strong positive sentiment (herd)
        herd_posts = [
            {"content": "This is great, amazing, bullish!"},
            {"content": "Excellent opportunity, very optimistic"},
            {"content": "Strong growth, positive outlook"},
            {"content": "Great news, rally incoming"},
            {"content": "Amazing results, bullish sentiment"},
        ]
        
        result = check_herd(herd_posts)
        
        assert "herd_detected" in result, "herd_detected not in result"
        assert "herd_score" in result, "herd_score not in result"
        assert "dominant_sentiment" in result, "dominant_sentiment not in result"
        assert result["herd_detected"] == True, f"Should detect herd, got {result}"
        assert result["dominant_sentiment"] == "positive", f"Expected positive, got {result['dominant_sentiment']}"
        
        print(f"✓ check_herd: detected={result['herd_detected']}, score={result['herd_score']}, sentiment={result['dominant_sentiment']}")
    
    def test_score_diversity(self):
        """Test that score_diversity calculates correctly"""
        from agents.critic import score_diversity
        
        # Diverse agents
        diverse_agents = [
            {"personality_type": "Skeptic"},
            {"personality_type": "Optimist"},
            {"personality_type": "Insider"},
            {"personality_type": "Contrarian"},
            {"personality_type": "Expert"},
        ]
        
        score = score_diversity(diverse_agents)
        
        assert isinstance(score, float), "score should be float"
        assert 0.0 <= score <= 1.0, f"score should be 0-1, got {score}"
        assert score > 0.8, f"Diverse agents should have high score, got {score}"
        
        print(f"✓ score_diversity: {score} for diverse agents")
        
        # Homogeneous agents
        homogeneous_agents = [
            {"personality_type": "Skeptic"},
            {"personality_type": "Skeptic"},
            {"personality_type": "Skeptic"},
        ]
        
        low_score = score_diversity(homogeneous_agents)
        assert low_score == 0.0, f"Homogeneous agents should have 0 score, got {low_score}"
        print(f"✓ score_diversity: {low_score} for homogeneous agents")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
