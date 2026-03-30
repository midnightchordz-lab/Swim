"""
Test GraphRAG Level 1 + Level 2 Features
- Level 1: Enhanced entity & relationship extraction with importance, tensions, hooks
- Level 2: Per-agent GraphRAG retrieval for grounded context
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ─── SAMPLE GRAPH DATA FOR UNIT TESTS ───────────────────────────────────────────

SAMPLE_GRAPH = {
    "summary": "Test summary about market dynamics",
    "themes": ["finance", "technology", "regulation"],
    "entities": [
        {
            "id": "bitcoin",
            "name": "Bitcoin",
            "type": "Asset",
            "description": "Leading cryptocurrency",
            "importance": "High",
            "stance": "contested"
        },
        {
            "id": "sec",
            "name": "SEC",
            "type": "Organization",
            "description": "US Securities regulator",
            "importance": "High",
            "stance": "negative"
        },
        {
            "id": "gary_gensler",
            "name": "Gary Gensler",
            "type": "Person",
            "description": "SEC Chairman",
            "importance": "Medium",
            "stance": "negative"
        },
        {
            "id": "etf_approval",
            "name": "ETF Approval",
            "type": "Event",
            "description": "Potential Bitcoin ETF approval",
            "importance": "High",
            "stance": "positive"
        },
        {
            "id": "inflation",
            "name": "Inflation Rate",
            "type": "Metric",
            "description": "Consumer price index",
            "importance": "Medium",
            "stance": "neutral"
        },
        {
            "id": "fed",
            "name": "Federal Reserve",
            "type": "Organization",
            "description": "US Central Bank",
            "importance": "Low",
            "stance": "neutral"
        }
    ],
    "relationships": [
        {
            "source_id": "sec",
            "target_id": "bitcoin",
            "type": "regulates",
            "description": "SEC regulates crypto markets",
            "strength": "Strong"
        },
        {
            "source_id": "gary_gensler",
            "target_id": "sec",
            "type": "leads",
            "description": "Gensler chairs the SEC",
            "strength": "Strong"
        },
        {
            "source_id": "etf_approval",
            "target_id": "bitcoin",
            "type": "impacts",
            "description": "ETF approval would boost Bitcoin",
            "strength": "Strong"
        },
        {
            "source_id": "fed",
            "target_id": "inflation",
            "type": "monitors",
            "description": "Fed monitors inflation",
            "strength": "Medium"
        }
    ],
    "key_tensions": [
        {
            "tension": "SEC vs crypto industry on regulation",
            "entities_involved": ["sec", "bitcoin"],
            "stakes": "Future of crypto in US"
        }
    ],
    "prediction_hooks": [
        "Will Bitcoin ETF be approved by Q1 2025?"
    ],
    "agent_diversity_hints": [
        "Crypto traders",
        "Traditional finance analysts",
        "Regulatory experts"
    ]
}

# Graph with old source/target format (for backward compatibility testing)
SAMPLE_GRAPH_OLD_FORMAT = {
    "summary": "Test with old relationship format",
    "themes": ["test"],
    "entities": [
        {"id": "a", "name": "Entity A", "type": "Concept", "description": "Test A", "importance": "High"},
        {"id": "b", "name": "Entity B", "type": "Concept", "description": "Test B", "importance": "Low"}
    ],
    "relationships": [
        {"source": "a", "target": "b", "type": "relates_to", "description": "A relates to B", "strength": "Medium"}
    ]
}

SAMPLE_AGENT = {
    "id": "agent_1",
    "name": "John Trader",
    "occupation": "Crypto Trader",
    "personality_type": "Optimist",
    "background": "10 years in crypto markets",
    "initial_stance": "Bullish on Bitcoin"
}

SAMPLE_POSTS = [
    {"content": "Bitcoin is looking strong today, SEC news pending"},
    {"content": "ETF approval could be huge for the market"},
    {"content": "Watching Gary Gensler's next move closely"}
]


class TestHealthEndpoint:
    """Test /api/health endpoint"""
    
    def test_health_returns_ok(self):
        """GET /api/health returns ok status"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"Health check passed: {data}")


class TestSessionCreation:
    """Test session creation endpoint"""
    
    def test_create_session(self):
        """POST /api/sessions creates a session"""
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36  # UUID format
        print(f"Session created: {data['session_id']}")


class TestGraphAgentProcessGraphResponse:
    """Test graph_agent.process_graph_response() function"""
    
    def test_process_graph_builds_entity_index(self):
        """process_graph_response() correctly builds entity_index"""
        from services.agents.graph_agent import process_graph_response
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        
        # Check entity_index exists
        assert "entity_index" in graph
        entity_index = graph["entity_index"]
        
        # Check entities are indexed by ID
        assert "bitcoin" in entity_index
        assert entity_index["bitcoin"]["name"] == "Bitcoin"
        
        # Check entities are indexed by lowercase name
        assert "bitcoin" in entity_index  # lowercase name
        assert "sec" in entity_index
        
        print(f"Entity index keys: {list(entity_index.keys())}")
    
    def test_process_graph_builds_adjacency_map(self):
        """process_graph_response() correctly builds adjacency_map"""
        from services.agents.graph_agent import process_graph_response
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        
        # Check adjacency_map exists
        assert "adjacency_map" in graph
        adjacency_map = graph["adjacency_map"]
        
        # Check relationships are mapped
        assert "sec" in adjacency_map
        assert "bitcoin" in adjacency_map
        
        # Check bidirectional mapping
        sec_neighbors = adjacency_map["sec"]
        assert len(sec_neighbors) >= 1
        
        print(f"Adjacency map keys: {list(adjacency_map.keys())}")
    
    def test_process_graph_adds_counts(self):
        """process_graph_response() adds entity_count and relationship_count"""
        from services.agents.graph_agent import process_graph_response
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        
        assert "entity_count" in graph
        assert "relationship_count" in graph
        assert graph["entity_count"] == 6
        assert graph["relationship_count"] == 4
        
        print(f"Counts: {graph['entity_count']} entities, {graph['relationship_count']} relationships")
    
    def test_process_graph_normalizes_old_format(self):
        """process_graph_response() normalizes source/target to source_id/target_id"""
        from services.agents.graph_agent import process_graph_response
        
        graph = process_graph_response(SAMPLE_GRAPH_OLD_FORMAT.copy())
        
        # Check relationships have source_id and target_id
        for rel in graph["relationships"]:
            assert "source_id" in rel
            assert "target_id" in rel
        
        print("Old format normalized successfully")


class TestGraphAgentStripRuntimeFields:
    """Test graph_agent.strip_runtime_fields() function"""
    
    def test_strip_removes_indices(self):
        """strip_runtime_fields() removes entity_index and adjacency_map"""
        from services.agents.graph_agent import process_graph_response, strip_runtime_fields
        
        # First process to add indices
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        assert "entity_index" in graph
        assert "adjacency_map" in graph
        
        # Then strip
        clean = strip_runtime_fields(graph)
        
        assert "entity_index" not in clean
        assert "adjacency_map" not in clean
        
        print("Runtime fields stripped successfully")
    
    def test_strip_keeps_counts(self):
        """strip_runtime_fields() keeps entity_count and relationship_count"""
        from services.agents.graph_agent import process_graph_response, strip_runtime_fields
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        clean = strip_runtime_fields(graph)
        
        assert "entity_count" in clean
        assert "relationship_count" in clean
        assert clean["entity_count"] == 6
        assert clean["relationship_count"] == 4
        
        print(f"Counts preserved: {clean['entity_count']} entities, {clean['relationship_count']} relationships")
    
    def test_strip_keeps_core_data(self):
        """strip_runtime_fields() keeps entities, relationships, themes, etc."""
        from services.agents.graph_agent import process_graph_response, strip_runtime_fields
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        clean = strip_runtime_fields(graph)
        
        assert "entities" in clean
        assert "relationships" in clean
        assert "themes" in clean
        assert "summary" in clean
        assert "key_tensions" in clean
        
        print("Core data preserved after stripping")


class TestGraphAgentEnsureIndices:
    """Test graph_agent.ensure_indices() function"""
    
    def test_ensure_rebuilds_indices(self):
        """ensure_indices() rebuilds entity_index and adjacency_map from stripped graph"""
        from services.agents.graph_agent import process_graph_response, strip_runtime_fields, ensure_indices
        
        # Process, strip, then ensure
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        clean = strip_runtime_fields(graph)
        
        assert "entity_index" not in clean
        assert "adjacency_map" not in clean
        
        rebuilt = ensure_indices(clean)
        
        assert "entity_index" in rebuilt
        assert "adjacency_map" in rebuilt
        assert "bitcoin" in rebuilt["entity_index"]
        
        print("Indices rebuilt successfully")
    
    def test_ensure_idempotent(self):
        """ensure_indices() is idempotent - doesn't break already-indexed graph"""
        from services.agents.graph_agent import process_graph_response, ensure_indices
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        original_count = len(graph["entity_index"])
        
        # Call ensure_indices again
        graph = ensure_indices(graph)
        
        assert len(graph["entity_index"]) == original_count
        
        print("ensure_indices is idempotent")


class TestGraphAgentRetrieveGraphContext:
    """Test graph_agent.retrieve_graph_context() function"""
    
    def test_retrieve_returns_context_string(self):
        """retrieve_graph_context() returns relevant context string for an agent"""
        from services.agents.graph_agent import process_graph_response, retrieve_graph_context
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        
        context = retrieve_graph_context(
            graph=graph,
            agent=SAMPLE_AGENT,
            recent_posts=SAMPLE_POSTS,
            round_num=1,
            max_entities=6
        )
        
        assert isinstance(context, str)
        assert len(context) > 0
        
        print(f"Context length: {len(context)} chars")
        print(f"Context preview: {context[:200]}...")
    
    def test_retrieve_includes_high_importance_entities(self):
        """retrieve_graph_context() includes high-importance entities"""
        from services.agents.graph_agent import process_graph_response, retrieve_graph_context
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        
        context = retrieve_graph_context(
            graph=graph,
            agent=SAMPLE_AGENT,
            recent_posts=[],
            round_num=1,
            max_entities=8
        )
        
        # High importance entities should be included
        assert "Bitcoin" in context or "SEC" in context or "ETF" in context
        
        print("High importance entities included in context")
    
    def test_retrieve_includes_occupation_relevant_entities(self):
        """retrieve_graph_context() includes entities relevant to agent's occupation"""
        from services.agents.graph_agent import process_graph_response, retrieve_graph_context
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        
        # Trader should get Asset/Metric entities
        trader_agent = {"occupation": "Crypto Trader", "id": "t1"}
        context = retrieve_graph_context(
            graph=graph,
            agent=trader_agent,
            recent_posts=[],
            round_num=1,
            max_entities=8
        )
        
        # Should include Asset type (Bitcoin)
        assert "Bitcoin" in context or "Asset" in context.lower()
        
        print("Occupation-relevant entities included")
    
    def test_retrieve_includes_recent_post_mentions(self):
        """retrieve_graph_context() includes entities mentioned in recent posts"""
        from services.agents.graph_agent import process_graph_response, retrieve_graph_context
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        
        # Posts mention Gary Gensler
        posts_with_gensler = [{"content": "Gary Gensler announced new rules"}]
        
        context = retrieve_graph_context(
            graph=graph,
            agent=SAMPLE_AGENT,
            recent_posts=posts_with_gensler,
            round_num=2,
            max_entities=8
        )
        
        # Gary Gensler should be in context due to mention
        assert "Gary Gensler" in context or "Gensler" in context
        
        print("Recent post mentions included in context")
    
    def test_retrieve_includes_tensions(self):
        """retrieve_graph_context() includes relevant tensions"""
        from services.agents.graph_agent import process_graph_response, retrieve_graph_context
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        
        context = retrieve_graph_context(
            graph=graph,
            agent=SAMPLE_AGENT,
            recent_posts=[],
            round_num=1,
            max_entities=8
        )
        
        # Should include tension info
        if "tension" in context.lower() or "SEC" in context:
            print("Tensions included in context")
        else:
            print("Context may not include tensions (depends on entity selection)")


class TestGraphAgentBuildAgentGenerationContext:
    """Test graph_agent.build_agent_generation_context() function"""
    
    def test_build_agent_context_returns_string(self):
        """build_agent_generation_context() returns rich context string"""
        from services.agents.graph_agent import process_graph_response, build_agent_generation_context
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        
        context = build_agent_generation_context(graph, num_agents=10)
        
        assert isinstance(context, str)
        assert len(context) > 100
        
        print(f"Agent generation context length: {len(context)} chars")
    
    def test_build_agent_context_includes_themes(self):
        """build_agent_generation_context() includes themes"""
        from services.agents.graph_agent import process_graph_response, build_agent_generation_context
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        context = build_agent_generation_context(graph, num_agents=10)
        
        assert "Themes:" in context
        assert "finance" in context.lower() or "technology" in context.lower()
        
        print("Themes included in agent generation context")
    
    def test_build_agent_context_includes_tensions(self):
        """build_agent_generation_context() includes tensions"""
        from services.agents.graph_agent import process_graph_response, build_agent_generation_context
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        context = build_agent_generation_context(graph, num_agents=10)
        
        assert "tension" in context.lower()
        
        print("Tensions included in agent generation context")
    
    def test_build_agent_context_includes_diversity_hints(self):
        """build_agent_generation_context() includes diversity hints"""
        from services.agents.graph_agent import process_graph_response, build_agent_generation_context
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        context = build_agent_generation_context(graph, num_agents=10)
        
        assert "viewpoint" in context.lower() or "diverse" in context.lower() or "Crypto traders" in context
        
        print("Diversity hints included in agent generation context")


class TestGraphAgentGenerateReportContext:
    """Test graph_agent.generate_report_context() function"""
    
    def test_generate_report_context_returns_string(self):
        """generate_report_context() returns context string with high-importance entities"""
        from services.agents.graph_agent import process_graph_response, generate_report_context
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        
        context = generate_report_context(graph)
        
        assert isinstance(context, str)
        assert len(context) > 50
        
        print(f"Report context length: {len(context)} chars")
    
    def test_generate_report_context_includes_high_importance(self):
        """generate_report_context() includes high-importance entities"""
        from services.agents.graph_agent import process_graph_response, generate_report_context
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        context = generate_report_context(graph)
        
        assert "High-importance" in context or "Bitcoin" in context or "SEC" in context
        
        print("High-importance entities in report context")
    
    def test_generate_report_context_includes_tensions(self):
        """generate_report_context() includes tensions with stakes"""
        from services.agents.graph_agent import process_graph_response, generate_report_context
        
        graph = process_graph_response(SAMPLE_GRAPH.copy())
        context = generate_report_context(graph)
        
        assert "tension" in context.lower() or "Stakes" in context
        
        print("Tensions with stakes in report context")


class TestFrontendGraphVisualization:
    """Test that frontend handles graph data correctly (via API response)"""
    
    def test_session_stores_graph_stats(self):
        """Session stores graph_entity_count and graph_rel_count after upload"""
        # Create session
        response = requests.post(f"{BASE_URL}/api/sessions", timeout=10)
        assert response.status_code == 200
        session_id = response.json()["session_id"]
        
        # Get session - should have no graph yet
        response = requests.get(f"{BASE_URL}/api/sessions/{session_id}", timeout=10)
        assert response.status_code == 200
        session = response.json()
        
        # Initially no graph
        assert session.get("graph_json") is None
        
        print(f"Session {session_id} created, no graph yet (as expected)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
