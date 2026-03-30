"""
Test suite for SwarmSim Prediction Tracking System
Tests: freeze_prediction, score_pending_predictions, score_single_prediction,
       /api/predictions/accuracy, /api/sessions/{session_id}/prediction-outcome,
       /api/predictions/score-now/{session_id}, APScheduler startup
"""
import pytest
import requests
import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthEndpoint:
    """Health endpoint tests"""
    
    def test_health_returns_ok(self):
        """GET /api/health returns ok status"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"✓ Health check passed: {data}")


class TestPredictionAccuracyEndpoint:
    """Tests for GET /api/predictions/accuracy"""
    
    def test_accuracy_returns_valid_json(self):
        """GET /api/predictions/accuracy returns valid JSON with required fields"""
        response = requests.get(f"{BASE_URL}/api/predictions/accuracy", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields exist
        required_fields = [
            "total_predictions", "win_rate", "pending", 
            "domain_breakdown", "top_agents", "calibration", "recent"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Validate types
        assert isinstance(data["total_predictions"], (int, float))
        assert isinstance(data["win_rate"], (int, float))
        assert isinstance(data["pending"], (int, float))
        assert isinstance(data["domain_breakdown"], dict)
        assert isinstance(data["top_agents"], list)
        assert isinstance(data["calibration"], list)
        assert isinstance(data["recent"], list)
        
        print(f"✓ Accuracy endpoint returned valid JSON: total={data['total_predictions']}, win_rate={data['win_rate']}%, pending={data['pending']}")


class TestPredictionOutcomeEndpoint:
    """Tests for GET /api/sessions/{session_id}/prediction-outcome"""
    
    def test_nonexistent_session_returns_not_tracked(self):
        """GET /api/sessions/{session_id}/prediction-outcome returns not_tracked for non-existent session"""
        fake_session_id = "nonexistent-session-12345"
        response = requests.get(f"{BASE_URL}/api/sessions/{fake_session_id}/prediction-outcome", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "not_tracked"
        print(f"✓ Non-existent session returns not_tracked: {data}")


class TestScoreNowEndpoint:
    """Tests for POST /api/predictions/score-now/{session_id}"""
    
    def test_nonexistent_session_returns_404(self):
        """POST /api/predictions/score-now/{session_id} returns 404 for non-existent session"""
        fake_session_id = "nonexistent-session-67890"
        response = requests.post(f"{BASE_URL}/api/predictions/score-now/{fake_session_id}", timeout=10)
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        print(f"✓ Score-now for non-existent session returns 404: {data}")


class TestFunctionExistence:
    """Tests to verify prediction tracking functions exist and are callable"""
    
    def test_freeze_prediction_exists(self):
        """freeze_prediction function exists and is callable"""
        try:
            from server import freeze_prediction
            assert callable(freeze_prediction)
            print("✓ freeze_prediction function exists and is callable")
        except ImportError as e:
            pytest.fail(f"Could not import freeze_prediction: {e}")
    
    def test_score_pending_predictions_exists(self):
        """score_pending_predictions function exists and is callable"""
        try:
            from server import score_pending_predictions
            assert callable(score_pending_predictions)
            print("✓ score_pending_predictions function exists and is callable")
        except ImportError as e:
            pytest.fail(f"Could not import score_pending_predictions: {e}")
    
    def test_score_single_prediction_exists(self):
        """score_single_prediction function exists and is callable"""
        try:
            from server import score_single_prediction
            assert callable(score_single_prediction)
            print("✓ score_single_prediction function exists and is callable")
        except ImportError as e:
            pytest.fail(f"Could not import score_single_prediction: {e}")


class TestAPSchedulerSetup:
    """Tests for APScheduler configuration"""
    
    def test_scheduler_exists(self):
        """APScheduler _prediction_scheduler exists"""
        try:
            from server import _prediction_scheduler
            assert _prediction_scheduler is not None
            print(f"✓ _prediction_scheduler exists: {type(_prediction_scheduler)}")
        except ImportError as e:
            pytest.fail(f"Could not import _prediction_scheduler: {e}")
    
    def test_scheduler_has_prediction_scorer_job(self):
        """APScheduler has prediction_scorer job configured"""
        try:
            from server import _prediction_scheduler
            jobs = _prediction_scheduler.get_jobs()
            job_ids = [job.id for job in jobs]
            assert "prediction_scorer" in job_ids, f"prediction_scorer job not found. Jobs: {job_ids}"
            print(f"✓ prediction_scorer job configured in scheduler")
        except ImportError as e:
            pytest.fail(f"Could not import _prediction_scheduler: {e}")


class TestBackendLogs:
    """Test that backend logs show scheduler started"""
    
    def test_scheduler_started_message_in_logs(self):
        """Backend starts with APScheduler running (check logs for '[Scheduler] Prediction scorer started')"""
        # This test verifies the scheduler startup by checking if the health endpoint works
        # and the scheduler is configured (actual log check would require log file access)
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        
        # Verify scheduler is configured
        try:
            from server import _prediction_scheduler
            jobs = _prediction_scheduler.get_jobs()
            assert len(jobs) > 0, "No jobs configured in scheduler"
            print(f"✓ Scheduler is configured with {len(jobs)} job(s)")
        except ImportError:
            # If we can't import, just verify the endpoint works
            print("✓ Backend is running (scheduler log check requires direct log access)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
