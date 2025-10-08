"""
Edge case tests
Tests unusual but valid scenarios
"""
import pytest
from unittest.mock import patch, Mock
import time


@pytest.mark.edge_case
class TestEdgeCases:
    """Test unusual but valid scenarios"""
    
    def test_very_long_video_id(self, client, mock_successful_extraction):
        """Test 1: Very long video ID (100 chars)"""
        # 100-character video ID
        long_video_id = "a" * 100
        
        response = client.get(f"/transcript/{long_video_id}")
        
        # Should pass to API (API will validate)
        # Either succeeds or returns 404
        assert response.status_code in [200, 404]
    
    def test_video_id_with_special_characters(self, client, mock_successful_extraction):
        """Test 2: Video ID with underscore and dash"""
        video_id = "abc-123_XYZ"
        
        response = client.get(f"/transcript/{video_id}")
        
        # Should work correctly
        assert response.status_code == 200
        data = response.json()
        
        # Video ID preserved exactly
        assert data["videoId"] == video_id
    
    @pytest.mark.slow
    def test_transcript_with_10000_segments(self, client, monkeypatch):
        """Test 3: Very long transcript (10,000 segments)"""
        # Create 10,000 segments
        large_segments = [
            {"text": f"Segment {i}", "start": float(i), "duration": 1.0}
            for i in range(10000)
        ]
        
        def mock_extract(video_id: str, language: str = "en"):
            transcript_text = " ".join([seg["text"] for seg in large_segments])
            return True, transcript_text, large_segments
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract)
        
        start_time = time.time()
        response = client.get("/transcript/test_video")
        elapsed_time = time.time() - start_time
        
        # Should complete in reasonable time (< 5 seconds)
        assert response.status_code == 200
        assert elapsed_time < 5.0
        
        data = response.json()
        assert data["success"] is True
    
    def test_segment_with_very_long_text(self, client, monkeypatch):
        """Test 4: Single segment with 10,000 characters of text"""
        # 10KB of text in one segment
        long_text = "a" * 10000
        
        segments = [
            {"text": long_text, "start": 0.0, "duration": 60.0}
        ]
        
        def mock_extract(video_id: str, language: str = "en"):
            transcript_text = " ".join([seg["text"] for seg in segments])
            return True, transcript_text, segments
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract)
        
        response = client.get("/transcript/test_video")
        
        # Should handle correctly
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["transcript"]) == 10000
    
    def test_empty_string_language_code(self, client, monkeypatch):
        """Test 5: Empty string language code"""
        call_log = []
        
        def mock_extract(video_id: str, language: str = "en"):
            call_log.append(language)
            return True, "test transcript", [{"text": "test", "start": 0.0, "duration": 1.0}]
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract)
        
        response = client.get("/transcript/test_video?lang=")
        
        # Should pass empty string to API or default to "en"
        assert response.status_code in [200, 404]
        
        if call_log:
            # Verify what language was passed
            assert call_log[0] in ["", "en"]
    
    def test_language_code_with_dash(self, client, monkeypatch):
        """Test 6: Language code with special characters (en-US)"""
        call_log = []
        
        def mock_extract(video_id: str, language: str = "en"):
            call_log.append(language)
            return True, "test transcript", [{"text": "test", "start": 0.0, "duration": 1.0}]
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract)
        
        response = client.get("/transcript/test_video?lang=en-US")
        
        # Should pass to API correctly
        assert response.status_code == 200
        
        # Verify "en-US" was passed through
        assert call_log[0] == "en-US"
    
    def test_float_precision_in_timestamps(self):
        """Test 7: Float precision in timestamp calculations"""
        from app import format_timestamp
        
        # Float precision issue: 0.1 + 0.2 = 0.30000000000000004
        imprecise_value = 0.1 + 0.2
        
        result = format_timestamp(imprecise_value)
        
        # Should display as "0.300" not "0.30000000004"
        assert result == "00:00:00.300"
    
    def test_video_id_with_spaces(self, client, mock_successful_extraction):
        """Test 8: Video ID with spaces (URL encoded)"""
        # FastAPI will decode URL-encoded spaces
        response = client.get("/transcript/abc%20123")
        
        # Should handle or reject gracefully
        # Either passes through or returns error
        assert response.status_code in [200, 404, 422]
    
    def test_null_vs_empty_string_handling(self, client, monkeypatch):
        """Test 9: Difference between None, empty string, and missing values"""
        segments_with_empty = [
            {"text": "", "start": 0.0, "duration": 1.0},
            {"text": "world", "start": 1.0, "duration": 1.0}
        ]
        
        def mock_extract(video_id: str, language: str = "en"):
            transcript_text = " ".join([seg["text"] for seg in segments_with_empty])
            return True, transcript_text, segments_with_empty
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract)
        
        response = client.get("/transcript/test_video")
        
        # Should handle empty strings correctly
        assert response.status_code == 200
        data = response.json()
        
        # Empty string should be in transcript (creates extra space)
        assert data["transcript"] == " world"
    
    def test_root_endpoint_documentation(self, client):
        """Test 10: Root endpoint returns API documentation"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have service info
        assert "service" in data
        assert "version" in data
        assert "endpoints" in data
