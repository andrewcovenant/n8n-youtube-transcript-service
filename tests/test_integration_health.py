"""
Integration tests for GET /health endpoint
Tests the health check endpoint
"""
import pytest
import time


@pytest.mark.integration
class TestHealthEndpoint:
    """Test GET /health endpoint"""
    
    def test_health_endpoint_returns_200(self, client):
        """Test 1: Health endpoint returns 200 status"""
        response = client.get("/health")
        
        # Verify successful response
        assert response.status_code == 200
    
    def test_health_endpoint_returns_correct_json(self, client):
        """Test 2: Health endpoint returns correct JSON structure"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify exact response
        assert data == {"status": "healthy"}
        
        # Verify it has only this one field
        assert len(data) == 1
        assert "status" in data
    
    def test_health_endpoint_works_when_youtube_down(self, client, monkeypatch):
        """Test 3: Health endpoint works even when YouTube API is down"""
        # Mock YouTube API to be unavailable
        def mock_failing_extract(video_id: str, language: str = "en"):
            raise Exception("YouTube API is down")
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_failing_extract)
        
        # Health check should still work (doesn't depend on external services)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_endpoint_is_fast(self, client):
        """Test 4: Health endpoint responds quickly (< 100ms)"""
        start_time = time.time()
        response = client.get("/health")
        elapsed_time = time.time() - start_time
        
        # Should be very fast
        assert response.status_code == 200
        assert elapsed_time < 0.1  # Less than 100ms
