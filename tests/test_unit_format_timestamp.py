"""
Unit tests for format_timestamp() function
Tests timestamp formatting with various inputs
"""
import pytest
from app import format_timestamp


@pytest.mark.unit
class TestFormatTimestamp:
    """Test the format_timestamp helper function"""
    
    def test_zero_seconds(self):
        """Test 1: Zero seconds should format as 00:00:00.000"""
        result = format_timestamp(0.0)
        assert result == "00:00:00.000"
    
    def test_under_one_minute(self):
        """Test 2: Under one minute - common case for short clips"""
        result = format_timestamp(45.5)
        assert result == "00:00:45.500"
    
    def test_exactly_one_minute(self):
        """Test 3: Exactly one minute - boundary condition"""
        result = format_timestamp(60.0)
        assert result == "00:01:00.000"
    
    def test_minutes_and_seconds(self):
        """Test 4: Minutes and seconds - common case for normal segments"""
        result = format_timestamp(125.75)  # 2 minutes, 5.75 seconds
        assert result == "00:02:05.750"
    
    def test_exactly_one_hour(self):
        """Test 5: Exactly one hour - boundary condition"""
        result = format_timestamp(3600.0)
        assert result == "01:00:00.000"
    
    def test_hours_minutes_seconds(self):
        """Test 6: Hours, minutes, and seconds - common case for long videos"""
        result = format_timestamp(3665.123)  # 1 hour, 1 minute, 5.123 seconds
        assert result == "01:01:05.123"
    
    def test_multiple_hours(self):
        """Test 7: Multiple hours - long video case"""
        result = format_timestamp(7384.5)  # 2 hours, 3 minutes, 4.5 seconds
        assert result == "02:03:04.500"
    
    def test_millisecond_precision(self):
        """Test 8: Millisecond precision - verify 3 decimal places preserved"""
        result = format_timestamp(0.123)
        assert result == "00:00:00.123"
