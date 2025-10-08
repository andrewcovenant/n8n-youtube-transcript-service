"""
Unit tests for proxy configuration logic
Tests get_api_instance() with various proxy configurations
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import os


@pytest.mark.unit
class TestProxyConfiguration:
    """Test get_api_instance() proxy configuration"""
    
    def test_no_proxy_credentials_direct_connection(self, monkeypatch):
        """Test 1: No proxy credentials should use direct connection"""
        monkeypatch.setenv("WEBSHARE_PROXY_USERNAME", "")
        monkeypatch.setenv("WEBSHARE_PROXY_PASSWORD", "")
        monkeypatch.setenv("PROXY_LOCATIONS", "")
        
        with patch('app.YouTubeTranscriptApi') as mock_api_class:
            from app import get_api_instance
            get_api_instance()
            
            # Verify YouTubeTranscriptApi was called without proxy_config
            mock_api_class.assert_called_once_with()
    
    def test_with_proxy_credentials(self, monkeypatch):
        """Test 2: With proxy credentials should create WebshareProxyConfig"""
        monkeypatch.setenv("WEBSHARE_PROXY_USERNAME", "testuser")
        monkeypatch.setenv("WEBSHARE_PROXY_PASSWORD", "testpass")
        monkeypatch.setenv("PROXY_LOCATIONS", "")
        
        with patch('app.WebshareProxyConfig') as mock_proxy_class, \
             patch('app.YouTubeTranscriptApi') as mock_api_class:
            
            from app import get_api_instance
            get_api_instance()
            
            # Verify WebshareProxyConfig was created with credentials
            mock_proxy_class.assert_called_once_with(
                proxy_username="testuser",
                proxy_password="testpass",
                filter_ip_locations=None
            )
            
            # Verify YouTubeTranscriptApi was called with proxy_config
            mock_api_class.assert_called_once()
            call_kwargs = mock_api_class.call_args[1]
            assert 'proxy_config' in call_kwargs
    
    def test_single_location_filter(self, monkeypatch):
        """Test 3: Single location filter"""
        monkeypatch.setenv("WEBSHARE_PROXY_USERNAME", "testuser")
        monkeypatch.setenv("WEBSHARE_PROXY_PASSWORD", "testpass")
        monkeypatch.setenv("PROXY_LOCATIONS", "us")
        
        with patch('app.WebshareProxyConfig') as mock_proxy_class, \
             patch('app.YouTubeTranscriptApi'):
            
            from app import get_api_instance
            get_api_instance()
            
            # Verify filter_ip_locations contains single country
            mock_proxy_class.assert_called_once()
            call_kwargs = mock_proxy_class.call_args[1]
            assert call_kwargs['filter_ip_locations'] == ["us"]
    
    def test_multiple_location_filter(self, monkeypatch):
        """Test 4: Multiple location filter"""
        monkeypatch.setenv("WEBSHARE_PROXY_USERNAME", "testuser")
        monkeypatch.setenv("WEBSHARE_PROXY_PASSWORD", "testpass")
        monkeypatch.setenv("PROXY_LOCATIONS", "us,de,gb")
        
        with patch('app.WebshareProxyConfig') as mock_proxy_class, \
             patch('app.YouTubeTranscriptApi'):
            
            from app import get_api_instance
            get_api_instance()
            
            # Verify filter_ip_locations contains all countries
            mock_proxy_class.assert_called_once()
            call_kwargs = mock_proxy_class.call_args[1]
            assert call_kwargs['filter_ip_locations'] == ["us", "de", "gb"]
    
    def test_location_filter_with_whitespace(self, monkeypatch):
        """Test 5: Location filter with whitespace should strip spaces"""
        monkeypatch.setenv("WEBSHARE_PROXY_USERNAME", "testuser")
        monkeypatch.setenv("WEBSHARE_PROXY_PASSWORD", "testpass")
        monkeypatch.setenv("PROXY_LOCATIONS", " us , de , gb ")
        
        with patch('app.WebshareProxyConfig') as mock_proxy_class, \
             patch('app.YouTubeTranscriptApi'):
            
            from app import get_api_instance
            get_api_instance()
            
            # Verify whitespace is stripped
            mock_proxy_class.assert_called_once()
            call_kwargs = mock_proxy_class.call_args[1]
            assert call_kwargs['filter_ip_locations'] == ["us", "de", "gb"]
    
    def test_location_filter_uppercase_conversion(self, monkeypatch):
        """Test 6: Location filter should convert to lowercase"""
        monkeypatch.setenv("WEBSHARE_PROXY_USERNAME", "testuser")
        monkeypatch.setenv("WEBSHARE_PROXY_PASSWORD", "testpass")
        monkeypatch.setenv("PROXY_LOCATIONS", "US,DE")
        
        with patch('app.WebshareProxyConfig') as mock_proxy_class, \
             patch('app.YouTubeTranscriptApi'):
            
            from app import get_api_instance
            get_api_instance()
            
            # Verify converted to lowercase
            mock_proxy_class.assert_called_once()
            call_kwargs = mock_proxy_class.call_args[1]
            assert call_kwargs['filter_ip_locations'] == ["us", "de"]
    
    def test_only_username_set_no_password(self, monkeypatch):
        """Test 7: Only username set (no password) should use direct connection"""
        monkeypatch.setenv("WEBSHARE_PROXY_USERNAME", "testuser")
        monkeypatch.setenv("WEBSHARE_PROXY_PASSWORD", "")
        monkeypatch.setenv("PROXY_LOCATIONS", "")
        
        with patch('app.YouTubeTranscriptApi') as mock_api_class:
            from app import get_api_instance
            get_api_instance()
            
            # Verify direct connection (no proxy_config)
            mock_api_class.assert_called_once_with()
