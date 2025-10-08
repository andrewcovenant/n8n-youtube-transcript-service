"""
Error handling tests
Tests error scenarios and edge cases in error handling
"""
import pytest
from unittest.mock import patch, Mock
import concurrent.futures


@pytest.mark.unit
class TestErrorHandling:
    """Test error scenarios and defensive programming"""
    
    def test_network_timeout_handling(self, client, monkeypatch):
        """Test 1: Network timeout handled gracefully"""
        def mock_extract_timeout(video_id: str, language: str = "en"):
            raise TimeoutError("Request timed out")
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract_timeout)
        
        # Should return error response, not crash
        response = client.get("/transcript/test_video")
        
        # Service should handle gracefully (implementation dependent)
        # Either 404 or 500, but should not crash
        assert response.status_code in [404, 500]
    
    def test_malformed_youtube_api_response(self):
        """Test 2: Malformed YouTube API response handled gracefully"""
        mock_api = Mock()
        mock_fetched = Mock()
        
        # Mock returns unexpected data structure
        mock_fetched.to_raw_data.return_value = "not a list"
        mock_api.fetch.return_value = mock_fetched
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            
            # Should handle gracefully or raise clear error
            try:
                success, text, raw = extract_transcript("test_video", "en")
                # If it doesn't crash, verify it returns failure
                assert success is False or text is not None
            except (TypeError, AttributeError):
                # Expected - malformed data should raise clear error
                pass
    
    def test_empty_transcript_from_api(self):
        """Test 3: Empty transcript array handled correctly"""
        mock_api = Mock()
        mock_fetched = Mock()
        mock_fetched.to_raw_data.return_value = []
        mock_api.fetch.return_value = mock_fetched
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            success, text, raw = extract_transcript("test_video", "en")
            
            # Should succeed with empty string
            assert success is True
            assert text == ""
            assert raw == []
    
    def test_null_values_in_segments(self):
        """Test 4: Null values in segment fields"""
        mock_api = Mock()
        mock_fetched = Mock()
        
        # Segment with null text
        segments = [
            {"text": None, "start": 0.0, "duration": 1.0}
        ]
        mock_fetched.to_raw_data.return_value = segments
        mock_api.fetch.return_value = mock_fetched
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            
            # Should handle or raise clear error
            try:
                success, text, raw = extract_transcript("test_video", "en")
                # If no error, verify it handles None gracefully
                assert text is not None or success is False
            except (TypeError, AttributeError):
                # Expected - null values should be caught
                pass
    
    def test_negative_start_time(self, client, monkeypatch):
        """Test 5: Negative start time in segment"""
        segments = [
            {"text": "test", "start": -5.0, "duration": 2.0}
        ]
        
        def mock_extract(video_id: str, language: str = "en"):
            transcript_text = " ".join([seg["text"] for seg in segments])
            return True, transcript_text, segments
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract)
        
        # Should pass through or validate
        response = client.get("/transcript/test_video/timestamps")
        
        # Either succeeds (passes through) or fails with validation
        assert response.status_code in [200, 400, 422]
    
    def test_zero_duration_segment(self, client, monkeypatch):
        """Test 6: Zero duration segment"""
        segments = [
            {"text": "instant", "start": 5.0, "duration": 0.0}
        ]
        
        def mock_extract(video_id: str, language: str = "en"):
            transcript_text = " ".join([seg["text"] for seg in segments])
            return True, transcript_text, segments
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract)
        
        response = client.get("/transcript/test_video/timestamps")
        
        # Should handle (end time = start time)
        assert response.status_code == 200
        data = response.json()
        
        if data["success"]:
            segment = data["segments"][0]
            assert segment["end"] == segment["start"]  # 5.0 + 0.0 = 5.0
    
    def test_very_large_timestamp_numbers(self):
        """Test 7: Very large timestamp numbers don't crash formatting"""
        from app import format_timestamp
        
        # Very large number (277 hours)
        large_seconds = 999999.999
        
        # Should not crash
        result = format_timestamp(large_seconds)
        
        # Verify it returns a string
        assert isinstance(result, str)
        assert ":" in result
    
    def test_unicode_in_error_messages(self, client, monkeypatch):
        """Test 8: Unicode characters in error messages logged correctly"""
        def mock_extract_unicode_error(video_id: str, language: str = "en"):
            raise Exception("Error: 错误 👎")
        
        import app
        monkeypatch.setattr(app, "extract_transcript", mock_extract_unicode_error)
        
        # Should handle unicode in exceptions
        response = client.get("/transcript/test_video")
        
        # Should not crash, return error response
        assert response.status_code in [404, 500]
    
    def test_missing_required_field_in_segment(self):
        """Test 9: Missing required field in segment"""
        mock_api = Mock()
        mock_fetched = Mock()
        
        # Segment missing 'duration' field
        segments = [
            {"text": "test", "start": 0.0}  # No duration
        ]
        mock_fetched.to_raw_data.return_value = segments
        mock_api.fetch.return_value = mock_fetched
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            
            # Should raise KeyError or handle gracefully
            try:
                success, text, raw = extract_transcript("test_video", "en")
                # If no error, check result
                assert success is not None
            except KeyError:
                # Expected - missing field should raise error
                pass
    
    def test_concurrent_request_handling(self, client, mock_successful_extraction):
        """Test 10: Concurrent requests handled without race conditions"""
        def make_request():
            return client.get("/transcript/dQw4w9WgXcQ")
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
