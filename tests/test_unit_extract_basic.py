"""
Unit tests for extract_transcript() basic functionality
Tests core extraction logic without retry mechanisms
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    InvalidVideoId
)


@pytest.mark.unit
class TestExtractTranscriptBasic:
    """Test extract_transcript() basic functionality"""
    
    def test_successful_extraction_first_attempt(self, sample_transcript_data):
        """Test 1: Successful extraction on first attempt"""
        mock_api = Mock()
        mock_fetched = Mock()
        mock_fetched.to_raw_data.return_value = sample_transcript_data
        mock_api.fetch.return_value = mock_fetched
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            success, text, raw = extract_transcript("test_video_id", "en")
            
            # Verify successful extraction
            assert success is True
            assert text == "Hello world this is a test"
            assert raw == sample_transcript_data
            
            # Verify API called exactly once (no retries)
            mock_api.fetch.assert_called_once_with("test_video_id", languages=["en"])
    
    def test_transcript_with_multiple_segments(self):
        """Test 2: Transcript with multiple segments joined correctly"""
        segments = [
            {"text": "seg1", "start": 0.0, "duration": 1.0},
            {"text": "seg2", "start": 1.0, "duration": 1.0},
            {"text": "seg3", "start": 2.0, "duration": 1.0},
            {"text": "seg4", "start": 3.0, "duration": 1.0},
            {"text": "seg5", "start": 4.0, "duration": 1.0}
        ]
        
        mock_api = Mock()
        mock_fetched = Mock()
        mock_fetched.to_raw_data.return_value = segments
        mock_api.fetch.return_value = mock_fetched
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            success, text, raw = extract_transcript("test_video", "en")
            
            # Verify text joined with single space
            assert text == "seg1 seg2 seg3 seg4 seg5"
    
    def test_transcript_with_empty_segment(self):
        """Test 3: Transcript with empty segment text"""
        segments = [
            {"text": "Hello", "start": 0.0, "duration": 1.0},
            {"text": "", "start": 1.0, "duration": 1.0},
            {"text": "world", "start": 2.0, "duration": 1.0}
        ]
        
        mock_api = Mock()
        mock_fetched = Mock()
        mock_fetched.to_raw_data.return_value = segments
        mock_api.fetch.return_value = mock_fetched
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            success, text, raw = extract_transcript("test_video", "en")
            
            # Empty string included in join
            assert success is True
            assert text == "Hello  world"  # Double space where empty segment was
    
    def test_alternative_language_spanish(self, sample_transcript_spanish):
        """Test 4: Extract transcript in Spanish"""
        mock_api = Mock()
        mock_fetched = Mock()
        mock_fetched.to_raw_data.return_value = sample_transcript_spanish
        mock_api.fetch.return_value = mock_fetched
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            success, text, raw = extract_transcript("test_video", "es")
            
            # Verify Spanish transcript
            assert success is True
            assert text == "Hola mundo esto es una prueba"
            
            # Verify API called with Spanish language
            mock_api.fetch.assert_called_once_with("test_video", languages=["es"])
    
    def test_transcripts_disabled_exception(self):
        """Test 5: TranscriptsDisabled exception returns failure immediately"""
        mock_api = Mock()
        mock_api.fetch.side_effect = TranscriptsDisabled("test_video")
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            success, text, raw = extract_transcript("test_video", "en")
            
            # Verify failure response
            assert success is False
            assert text is None
            assert raw is None
    
    def test_no_transcript_found_exception(self):
        """Test 6: NoTranscriptFound exception returns failure immediately"""
        mock_api = Mock()
        mock_api.fetch.side_effect = NoTranscriptFound(
            "test_video", ["en"], []
        )
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            success, text, raw = extract_transcript("test_video", "en")
            
            # Verify failure response
            assert success is False
            assert text is None
            assert raw is None
    
    def test_video_unavailable_exception(self):
        """Test 7: VideoUnavailable exception returns failure immediately"""
        mock_api = Mock()
        mock_api.fetch.side_effect = VideoUnavailable("test_video")
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            success, text, raw = extract_transcript("test_video", "en")
            
            # Verify failure response
            assert success is False
            assert text is None
            assert raw is None
    
    def test_invalid_video_id_exception(self):
        """Test 8: InvalidVideoId exception returns failure immediately"""
        mock_api = Mock()
        mock_api.fetch.side_effect = InvalidVideoId("invalid_id")
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            success, text, raw = extract_transcript("invalid_id", "en")
            
            # Verify failure response
            assert success is False
            assert text is None
            assert raw is None
    
    def test_transcript_with_special_characters(self, sample_transcript_unicode):
        """Test 9: Transcript with emojis and unicode preserved"""
        mock_api = Mock()
        mock_fetched = Mock()
        mock_fetched.to_raw_data.return_value = sample_transcript_unicode
        mock_api.fetch.return_value = mock_fetched
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            success, text, raw = extract_transcript("test_video", "en")
            
            # Verify special characters preserved
            assert success is True
            assert "👋" in text
            assert "世界" in text
            assert "Привет" in text
    
    def test_very_long_transcript_performance(self):
        """Test 10: Very long transcript (1000 segments) performs acceptably"""
        import time
        
        # Create 1000 segments
        segments = [
            {"text": f"Segment {i}", "start": float(i), "duration": 1.0}
            for i in range(1000)
        ]
        
        mock_api = Mock()
        mock_fetched = Mock()
        mock_fetched.to_raw_data.return_value = segments
        mock_api.fetch.return_value = mock_fetched
        
        with patch('app.get_api_instance', return_value=mock_api):
            from app import extract_transcript
            
            start_time = time.time()
            success, text, raw = extract_transcript("test_video", "en")
            elapsed_time = time.time() - start_time
            
            # Verify success and performance
            assert success is True
            assert len(raw) == 1000
            assert elapsed_time < 1.0  # Should complete in under 1 second
