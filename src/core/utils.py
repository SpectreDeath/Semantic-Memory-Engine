import os
import yaml
from pathlib import Path

def load_config():
    """Loads the central configuration file."""
    config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_path(category, key):
    """Resolves paths from configuration."""
    config = load_config()
    return os.path.normpath(config[category][key])

def ensure_storage():
    """Ensures all configured storage directories exist."""
    config = load_config()
    for key, path in config['storage'].items():
        if key.endswith('_dir'):
            os.makedirs(path, exist_ok=True)
        elif key.endswith('_path'):
            os.makedirs(os.path.dirname(path), exist_ok=True)
