import os
import yaml
from typing import Dict, Any, Optional

class Config:
    """
    Configuration manager for the application.
    Loads configuration from YAML file and provides access to settings.
    """
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from YAML file"""
        config_path = os.environ.get(
            "CONFIG_PATH", 
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.yaml"))
        
        try:
            with open(config_path, 'r') as config_file:
                self._config = yaml.safe_load(config_file) or {}
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"Error loading configuration: {e}")
            self._config = {}
    
    def get(self, section: str, key: str, default=None) -> Any:
        """Get configuration value by section and key"""
        if section in self._config and key in self._config[section]:
            return self._config[section][key]
        return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self._config.get(section, {})
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self._config


# Create a singleton instance
config = Config()
