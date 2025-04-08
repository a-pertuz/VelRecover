"""Application configuration management."""

import os
import json
import appdirs

class AppConfig:
    """Handles application configuration and settings."""
    
    def __init__(self, app_name="velrecover"):
        """Initialize with default configuration values."""
        self.app_name = app_name
        self.user_data_dir = appdirs.user_data_dir(self.app_name)
        self.user_config_dir = appdirs.user_config_dir(self.app_name)
        
        # Ensure config directory exists
        os.makedirs(self.user_config_dir, exist_ok=True)
        self.config_path = os.path.join(self.user_config_dir, 'config.json')
        
        # Default configuration values
        self._config = {
            'base_dir': os.path.join(self.user_data_dir, 'data'),
            'last_data_dir': '',
            'last_segy_dir': '',
            'default_blur': 1
        }
        
        # Load existing configuration if available
        self.load()
        
        # If this is first run, create base directories right away
        if not os.path.exists(self.work_dir):
            self.create_directories()
    
    def load(self):
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Update only keys that exist in the default config
                    for key in self._config:
                        if key in loaded_config:
                            self._config[key] = loaded_config[key]
                return True
            except (json.JSONDecodeError, IOError):
                return False
        return False
    
    def save(self):
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
            return True
        except IOError:
            return False
    
    def get(self, key, default=None):
        """Get a configuration value with optional default."""
        return self._config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value."""
        self._config[key] = value
        return self.save()
    
    @property
    def work_dir(self):
        """Get the working directory."""
        return self._config['base_dir']
    
    @work_dir.setter
    def work_dir(self, value):
        """Set the working directory."""
        self._config['base_dir'] = value
        self.save()
    
    @property
    def vels_dir(self):
        """Get the velocities directory."""
        return os.path.join(self.work_dir, "VELS", "2D")
    
    @property
    def raw_vels_dir(self):
        """Get the raw velocities directory."""
        return os.path.join(self.work_dir, "VELS", "RAW")
    
    @property
    def segy_dir(self):
        """Get the SEGY directory."""
        return os.path.join(self.work_dir, "SEGY")
    
    @property
    def log_dir(self):
        """Get the log directory."""
        return os.path.join(self.work_dir, "LOG")
    
    def create_directories(self):
        """Create all required directories."""
        dirs = [
            self.work_dir,
            self.vels_dir,
            self.raw_vels_dir,
            self.segy_dir,
            self.log_dir
        ]
        
        created = []
        for directory in dirs:
            try:
                os.makedirs(directory, exist_ok=True)
                created.append(directory)
            except OSError:
                pass
        
        return created
