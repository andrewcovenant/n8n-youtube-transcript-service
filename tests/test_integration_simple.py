"""
Integration tests for GET /transcript/{video_id} endpoint
Tests the simple transcript endpoint
"""
import pytest
from unittest.mock import patch


@pytest.mark.integration
class TestSimpleTranscriptEndpoint:
    """Test GET /transcript/{video_id} endpoint"""
    
    def test_valid_video_default_language(self, client, mock_successful_extraction):
        """Test 1: Valid video with default language returns 200"""
        response = client.get("/transcript/dQw4w9WgXcQ")
        
        # Verify status and response
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["videoId"] == "dQw4w9WgXcQ"
        assert data["transcript"] is not None
        assert data["hasTranscript"] is True
        assert isinstance(data["transcript"], str)
    
    def test_valid_video_spanish_language(self, client, monkeypatch, sample_transcript_spanish):
        """Test 2: Valid video with Spanish language parameter"""
        def mock_extract(video_id: str, language: str = "en"):
            if language == "es":
                transcript_text = " ".join([seg["text"] for seg in sample_transcript_spanish])
                return True, transcript_text, sample_transcript_spanish
            return False, None, None
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract)
        
        response = client.get("/transcript/dQw4w9WgXcQ?lang=es")
        
        # Verify Spanish transcript returned
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "Hola" in data["transcript"] or "mundo" in data["transcript"]
    
    def test_invalid_video_id(self, client, mock_failed_extraction):
        """Test 3: Invalid video ID returns 404"""
        response = client.get("/transcript/invalid_video_123")
        
        # Verify 404 response
        assert response.status_code == 404
        data = response.json()
        
        assert data["success"] is False
        assert data["hasTranscript"] is False
    
    def test_video_without_transcript(self, client, mock_failed_extraction):
        """Test 4: Video without transcript returns 404"""
        response = client.get("/transcript/dQw4w9WgXcQ")
        
        # Verify 404 response
        assert response.status_code == 404
        data = response.json()
        
        assert data["success"] is False
        assert data["hasTranscript"] is False
        assert data["transcript"] is None
    
    def test_response_schema_validation_success(self, client, mock_successful_extraction):
        """Test 5: Success response has correct schema"""
        response = client.get("/transcript/dQw4w9WgXcQ")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields present
        assert "success" in data
        assert "videoId" in data
        assert "transcript" in data
        assert "hasTranscript" in data
        
        # Verify field types
        assert isinstance(data["success"], bool)
        assert isinstance(data["videoId"], str)
        assert isinstance(data["transcript"], str)
        assert isinstance(data["hasTranscript"], bool)
        
        # Verify no extra fields (only these 4)
        assert len(data) == 4
    
    def test_response_schema_validation_failure(self, client, mock_failed_extraction):
        """Test 6: Failure response has correct schema"""
        response = client.get("/transcript/invalid_id")
        
        assert response.status_code == 404
        data = response.json()
        
        # Verify required fields
        assert data["success"] is False
        assert data["videoId"] == "invalid_id"
        assert data["transcript"] is None
        assert data["hasTranscript"] is False
    
    def test_video_id_matches_input_exactly(self, client, mock_successful_extraction):
        """Test 7: Response videoId matches input exactly (no normalization)"""
        video_id = "AbC123-_XyZ"
        response = client.get(f"/transcript/{video_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify exact match (no case changes, no encoding)
        assert data["videoId"] == video_id
    
    def test_multiple_query_parameters(self, client, mock_successful_extraction):
        """Test 8: Extra query parameters are ignored gracefully"""
        response = client.get("/transcript/dQw4w9WgXcQ?lang=en&extra=ignored&foo=bar")
        
        # Should work correctly, extra params ignored
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["videoId"] == "dQw4w9WgXcQ"
