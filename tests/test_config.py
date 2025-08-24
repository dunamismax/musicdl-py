"""Tests for configuration management."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from musicdl.config import ConfigManager
from musicdl.core.models import AppConfig


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_config_manager_initialization(temp_config_dir):
    """Test configuration manager initialization."""
    config_path = temp_config_dir / "config.json"
    manager = ConfigManager(config_path)
    
    assert manager.config_path == config_path
    assert isinstance(manager.config, AppConfig)


def test_config_loading_default(temp_config_dir):
    """Test loading default configuration when file doesn't exist."""
    config_path = temp_config_dir / "config.json"
    manager = ConfigManager(config_path)
    
    config = manager.load()
    assert isinstance(config, AppConfig)
    assert config.max_concurrent_downloads == 1
    assert config.audio_format == "bestaudio/best"


def test_config_saving_and_loading(temp_config_dir):
    """Test saving and loading configuration."""
    config_path = temp_config_dir / "config.json"
    manager = ConfigManager(config_path)
    
    # Modify and save config
    config = manager.load()
    config.max_concurrent_downloads = 3
    config.audio_format = "mp3"
    manager.save()
    
    # Create new manager and load
    new_manager = ConfigManager(config_path)
    loaded_config = new_manager.load()
    
    assert loaded_config.max_concurrent_downloads == 3
    assert loaded_config.audio_format == "mp3"


def test_config_validation(temp_config_dir):
    """Test configuration validation."""
    config_path = temp_config_dir / "config.json"
    
    # Create invalid config file
    invalid_config = {
        "max_concurrent_downloads": "invalid",  # Should be int
        "audio_format": 123,  # Should be string
    }
    
    with open(config_path, 'w') as f:
        json.dump(invalid_config, f)
    
    manager = ConfigManager(config_path)
    # Should fall back to defaults when validation fails
    config = manager.load()
    assert config.max_concurrent_downloads == 1  # Default value
    assert config.audio_format == "bestaudio/best"  # Default value


def test_config_corrupted_file(temp_config_dir):
    """Test handling of corrupted configuration file."""
    config_path = temp_config_dir / "config.json"
    
    # Create corrupted JSON file
    with open(config_path, 'w') as f:
        f.write("invalid json {broken")
    
    manager = ConfigManager(config_path)
    config = manager.load()
    
    # Should fall back to defaults
    assert isinstance(config, AppConfig)
    assert config.max_concurrent_downloads == 1


def test_config_directory_creation(temp_config_dir):
    """Test automatic creation of config directory."""
    nested_path = temp_config_dir / "nested" / "config" / "config.json"
    
    manager = ConfigManager(nested_path)
    manager.save()
    
    assert nested_path.exists()
    assert nested_path.parent.is_dir()


def test_config_reset(temp_config_dir):
    """Test configuration reset functionality."""
    config_path = temp_config_dir / "config.json"
    manager = ConfigManager(config_path)
    
    # Modify config
    config = manager.load()
    config.max_concurrent_downloads = 5
    manager.save()
    
    # Reset and verify
    reset_config = manager.reset()
    assert reset_config.max_concurrent_downloads == 1  # Default


def test_config_path_resolution(temp_config_dir):
    """Test configuration path resolution."""
    config_path = temp_config_dir / "config.json"
    manager = ConfigManager(config_path)
    
    config = manager.load()
    
    # Paths should be resolved relative to config directory
    assert config.music_dir.is_absolute()
    assert config.cache_dir.is_absolute()
    assert config.logs_dir.is_absolute()


def test_config_ensure_directories(temp_config_dir):
    """Test directory creation for config paths."""
    config_path = temp_config_dir / "config.json"
    manager = ConfigManager(config_path)
    
    config = manager.load()
    
    # Directories should be created
    assert config.music_dir.exists()
    assert config.cache_dir.exists()
    assert config.logs_dir.exists()


def test_config_model_validation():
    """Test AppConfig model validation."""
    # Valid config
    config = AppConfig(
        max_concurrent_downloads=3,
        audio_format="mp3",
        show_clock=True
    )
    assert config.max_concurrent_downloads == 3
    assert config.audio_format == "mp3"
    assert config.show_clock is True
    
    # Test default values
    default_config = AppConfig()
    assert default_config.max_concurrent_downloads == 1
    assert default_config.overwrite_files is True
    assert default_config.show_clock is True


def test_config_forbidden_extra_fields():
    """Test that extra fields are forbidden in config."""
    with pytest.raises(Exception):  # Pydantic validation error
        AppConfig(unknown_field="value")


def test_config_serialization():
    """Test configuration serialization/deserialization."""
    config = AppConfig(
        max_concurrent_downloads=2,
        audio_format="aac",
        bitrate="256"
    )
    
    # Convert to dict
    config_dict = config.model_dump()
    assert config_dict["max_concurrent_downloads"] == 2
    assert config_dict["audio_format"] == "aac"
    
    # Create from dict
    new_config = AppConfig(**config_dict)
    assert new_config.max_concurrent_downloads == 2
    assert new_config.audio_format == "aac"


@patch('pathlib.Path.write_text')
def test_config_save_permission_error(mock_write, temp_config_dir):
    """Test handling of permission errors during save."""
    mock_write.side_effect = PermissionError("Access denied")
    
    config_path = temp_config_dir / "config.json"
    manager = ConfigManager(config_path)
    
    # Should not raise exception, just log error
    manager.save()  # Should complete without raising


def test_config_thread_safety(temp_config_dir):
    """Test basic thread safety of config operations."""
    import threading
    import time
    
    config_path = temp_config_dir / "config.json"
    manager = ConfigManager(config_path)
    
    results = []
    errors = []
    
    def worker(worker_id):
        try:
            for i in range(5):
                config = manager.load()
                config.max_concurrent_downloads = worker_id
                manager.save()
                time.sleep(0.01)  # Small delay
                loaded = manager.load()
                results.append(loaded.max_concurrent_downloads)
        except Exception as e:
            errors.append(e)
    
    # Run multiple threads
    threads = []
    for i in range(3):
        t = threading.Thread(target=worker, args=(i + 1,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Should not have any errors
    assert len(errors) == 0
    assert len(results) == 15  # 3 workers × 5 operations


def test_config_edge_case_values():
    """Test configuration with edge case values."""
    # Test minimum values
    config = AppConfig(max_concurrent_downloads=1)
    assert config.max_concurrent_downloads == 1
    
    # Test string trimming
    config = AppConfig(audio_format="  mp3  ")
    assert config.audio_format == "mp3"  # Should be trimmed
    
    # Test path handling
    config = AppConfig(music_dir=Path("relative/path"))
    assert isinstance(config.music_dir, Path)