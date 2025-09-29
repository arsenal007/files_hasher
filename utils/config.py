import os
import json

class Config:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.json")
        self.config_path = config_path
        self._config = None
        self.load()
        
    def load(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, "r") as f:
            self._config = json.load(f)

    def get(self, key, default=None):
        return self._config.get(key, default)

    def set(self, key, value):
        self._config[key] = value

    def save(self):
        with open(self.config_path, "w") as f:
            json.dump(self._config, f, indent=4)
            
    def get_config_path(self):
        return self.config_path
