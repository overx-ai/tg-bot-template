"""
Tests for the configuration system.
"""

import pytest
import os
import tempfile
import yaml
from bot.config import ConfigManager, BotConfig, FeatureConfig


def test_default_config():
    """Test that default configuration is created correctly."""
    config = BotConfig()
    
    assert config.name == "Generic Bot"
    assert config.description == "A configurable Telegram bot template"
    assert config.version == "0.1.0"
    assert isinstance(config.features, FeatureConfig)


def test_feature_config_defaults():
    """Test that feature configuration has correct defaults."""
    features = FeatureConfig()
    
    assert features.ai_assistant == False
    assert features.ai_provider == "openai"
    assert features.ai_model == "gpt-4"
    assert features.payments == False
    assert features.support_bot == False
    assert features.user_credits == True
    assert features.initial_credits == 1
    assert features.localization == True
    assert features.default_language == "en"
    assert "en" in features.supported_languages


def test_config_manager_with_yaml():
    """Test configuration manager with YAML files."""
    # Create temporary directory for config files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test features.yaml
        features_config = {
            "features": {
                "ai_assistant": {
                    "enabled": True,
                    "provider": "openai",
                    "model": "gpt-3.5-turbo"
                },
                "payments": {
                    "enabled": True,
                    "currency": "USD"
                }
            }
        }
        
        features_path = os.path.join(temp_dir, "features.yaml")
        with open(features_path, 'w') as f:
            yaml.dump(features_config, f)
        
        # Create a test bot_config.yaml
        bot_config = {
            "bot": {
                "name": "Test Bot",
                "description": "A test bot"
            }
        }
        
        bot_config_path = os.path.join(temp_dir, "bot_config.yaml")
        with open(bot_config_path, 'w') as f:
            yaml.dump(bot_config, f)
        
        # Test configuration loading
        config_manager = ConfigManager(temp_dir)
        config = config_manager.load_config()
        
        assert config.name == "Test Bot"
        assert config.description == "A test bot"
        assert config.features.ai_assistant == True
        assert config.features.ai_model == "gpt-3.5-turbo"
        assert config.features.payments == True


def test_config_manager_missing_files():
    """Test configuration manager with missing files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = ConfigManager(temp_dir)
        config = config_manager.load_config()
        
        # Should use defaults when files are missing
        assert config.name == "Generic Bot"
        assert config.features.ai_assistant == False


if __name__ == "__main__":
    pytest.main([__file__])