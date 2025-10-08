"""
Integration tests for POST /transcript endpoint
Tests the detailed transcript endpoint with raw segments
"""
import pytest
from unittest.mock import patch


@pytest.mark.integration
class TestDetailedTranscriptEndpoint:
    """Test POST /transcript endpoint"""
    
    def test_valid_request_with_video_id_and_language(self, client, mock_successful_extraction):
        """Test 1: Valid request with video_id and language"""
        request_body = {
            "video_id": "dQw4w9WgXcQ",
            "language": "en"
        }
        
        response = client.post("/transcript", json=request_body)
        
        # Verify successful response
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["videoId"] == "dQw4w9WgXcQ"
        assert data["transcript"] is not None
        assert data["raw"] is not None
        assert data["language"] == "en"
        
        # Verify raw segments structure
        assert isinstance(data["raw"], list)
        assert len(data["raw"]) > 0
    
    def test_language_defaults_to_en_if_omitted(self, client, mock_successful_extraction):
        """Test 2: Language defaults to 'en' if omitted"""
        request_body = {
            "video_id": "dQw4w9WgXcQ"
        }
        
        response = client.post("/transcript", json=request_body)
        
        # Should use English by default
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["language"] == "en"
    
    def test_missing_video_id_in_body(self, client):
        """Test 3: Missing video_id returns 422 validation error"""
        request_body = {
            "language": "en"
        }
        
        response = client.post("/transcript", json=request_body)
        
        # Pydantic validation error
        assert response.status_code == 422
        data = response.json()
        
        # Check error mentions video_id field
        assert "detail" in data
    
    def test_empty_request_body(self, client):
        """Test 4: Empty request body returns 422 validation error"""
        request_body = {}
        
        response = client.post("/transcript", json=request_body)
        
        # Pydantic validation error
        assert response.status_code == 422
    
    def test_malformed_json(self, client):
        """Test 5: Malformed JSON returns 422 error"""
        response = client.post(
            "/transcript",
            content="{invalid json}",
            headers={"Content-Type": "application/json"}
        )
        
        # Should return error for malformed JSON
        assert response.status_code == 422
    
    def test_raw_segments_structure_validation(self, client, mock_successful_extraction, sample_transcript_data):
        """Test 6: Raw segments have correct structure"""
        request_body = {
            "video_id": "dQw4w9WgXcQ",
            "language": "en"
        }
        
        response = client.post("/transcript", json=request_body)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify each segment has required fields
        for segment in data["raw"]:
            assert "text" in segment
            assert "start" in segment
            assert "duration" in segment
            
            # Verify field types
            assert isinstance(segment["text"], str)
            assert isinstance(segment["start"], (int, float))
            assert isinstance(segment["duration"], (int, float))
    
    def test_invalid_video_in_post(self, client, mock_failed_extraction):
        """Test 7: Invalid video returns 404"""
        request_body = {
            "video_id": "invalid_video",
            "language": "en"
        }
        
        response = client.post("/transcript", json=request_body)
        
        # Should return 404
        assert response.status_code == 404
        data = response.json()
        
        assert data["success"] is False
        assert data["videoId"] == "invalid_video"
        assert data["transcript"] is None
        assert data["raw"] is None
    
    def test_extra_fields_in_body_ignored(self, client, mock_successful_extraction):
        """Test 8: Extra fields in body are ignored (Pydantic default)"""
        request_body = {
            "video_id": "dQw4w9WgXcQ",
            "language": "en",
            "extra": "field",
            "foo": "bar"
        }
        
        response = client.post("/transcript", json=request_body)
        
        # Should still work, extra fields ignored
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["videoId"] == "dQw4w9WgXcQ"
