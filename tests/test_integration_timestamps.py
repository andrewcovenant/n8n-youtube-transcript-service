"""
Integration tests for GET /transcript/{video_id}/timestamps endpoint
Tests the timestamped transcript endpoint
"""
import pytest
from unittest.mock import patch


@pytest.mark.integration
class TestTimestampedTranscriptEndpoint:
    """Test GET /transcript/{video_id}/timestamps endpoint"""
    
    def test_valid_video_returns_timestamped_segments(self, client, mock_successful_extraction, sample_transcript_data):
        """Test 1: Valid video returns timestamped segments"""
        response = client.get("/transcript/dQw4w9WgXcQ/timestamps")
        
        # Verify successful response
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["videoId"] == "dQw4w9WgXcQ"
        assert data["segments"] is not None
        assert isinstance(data["segments"], list)
        assert len(data["segments"]) == len(sample_transcript_data)
    
    def test_each_segment_has_required_fields(self, client, mock_successful_extraction):
        """Test 2: Each segment has all required fields"""
        response = client.get("/transcript/dQw4w9WgXcQ/timestamps")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify each segment structure
        for segment in data["segments"]:
            assert "text" in segment
            assert "start" in segment
            assert "end" in segment
            assert "startFormatted" in segment
            assert "endFormatted" in segment
            
            # Verify types
            assert isinstance(segment["text"], str)
            assert isinstance(segment["start"], (int, float))
            assert isinstance(segment["end"], (int, float))
            assert isinstance(segment["startFormatted"], str)
            assert isinstance(segment["endFormatted"], str)
    
    def test_end_time_calculation_correct(self, client, monkeypatch):
        """Test 3: End time = start + duration"""
        segments = [
            {"text": "Test", "start": 5.0, "duration": 2.5}
        ]
        
        def mock_extract(video_id: str, language: str = "en"):
            transcript_text = " ".join([seg["text"] for seg in segments])
            return True, transcript_text, segments
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract)
        
        response = client.get("/transcript/test_video/timestamps")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify end = start + duration
        segment = data["segments"][0]
        assert segment["start"] == 5.0
        assert segment["end"] == 7.5  # 5.0 + 2.5
    
    def test_start_timestamp_formatting(self, client, monkeypatch):
        """Test 4: Start timestamp formatted correctly"""
        segments = [
            {"text": "Test", "start": 125.5, "duration": 1.0}
        ]
        
        def mock_extract(video_id: str, language: str = "en"):
            transcript_text = " ".join([seg["text"] for seg in segments])
            return True, transcript_text, segments
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract)
        
        response = client.get("/transcript/test_video/timestamps")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify timestamp format (2 minutes, 5.5 seconds)
        segment = data["segments"][0]
        assert segment["startFormatted"] == "00:02:05.500"
    
    def test_end_timestamp_formatting(self, client, monkeypatch):
        """Test 5: End timestamp formatted correctly"""
        segments = [
            {"text": "Test", "start": 0.0, "duration": 3665.123}
        ]
        
        def mock_extract(video_id: str, language: str = "en"):
            transcript_text = " ".join([seg["text"] for seg in segments])
            return True, transcript_text, segments
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract)
        
        response = client.get("/transcript/test_video/timestamps")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify end timestamp (1 hour, 1 minute, 5.123 seconds)
        segment = data["segments"][0]
        assert segment["endFormatted"] == "01:01:05.123"
    
    def test_multiple_segments_are_sequential(self, client, mock_successful_extraction, sample_transcript_data):
        """Test 6: Multiple segments have sequential start times"""
        response = client.get("/transcript/dQw4w9WgXcQ/timestamps")
        
        assert response.status_code == 200
        data = response.json()
        
        segments = data["segments"]
        
        # Verify segments are in order
        for i in range(len(segments) - 1):
            assert segments[i]["start"] <= segments[i + 1]["start"]
    
    def test_language_parameter_works(self, client, monkeypatch, sample_transcript_spanish):
        """Test 7: Language parameter works correctly"""
        def mock_extract(video_id: str, language: str = "en"):
            if language == "es":
                transcript_text = " ".join([seg["text"] for seg in sample_transcript_spanish])
                return True, transcript_text, sample_transcript_spanish
            return False, None, None
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract)
        
        response = client.get("/transcript/dQw4w9WgXcQ/timestamps?lang=es")
        
        # Verify Spanish segments returned
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["segments"]) > 0
    
    def test_invalid_video_returns_404(self, client, mock_failed_extraction):
        """Test 8: Invalid video returns 404"""
        response = client.get("/transcript/invalid_video/timestamps")
        
        # Verify 404 response
        assert response.status_code == 404
        data = response.json()
        
        assert data["success"] is False
        assert data["segments"] is None
    
    def test_response_schema_for_success(self, client, mock_successful_extraction):
        """Test 9: Response schema correct for success"""
        response = client.get("/transcript/dQw4w9WgXcQ/timestamps")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "success" in data
        assert "videoId" in data
        assert "segments" in data
        assert "language" in data
        
        # Verify types
        assert isinstance(data["success"], bool)
        assert isinstance(data["videoId"], str)
        assert isinstance(data["segments"], list)
        assert isinstance(data["language"], str)
    
    def test_response_schema_for_failure(self, client, mock_failed_extraction):
        """Test 10: Response schema correct for 404"""
        response = client.get("/transcript/invalid_video/timestamps?lang=en")
        
        assert response.status_code == 404
        data = response.json()
        
        # Verify failure response
        assert data["success"] is False
        assert data["videoId"] == "invalid_video"
        assert data["segments"] is None
        assert data["language"] == "en"
