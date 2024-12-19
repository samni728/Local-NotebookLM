
import yaml
from pathlib import Path
from typing import Dict, Any

def read_config(config_path: str = "config.yaml") -> Dict[Any, Any]:
    """
    Read and parse a YAML configuration file.
    
    Args:
        config_path (str): Path to the YAML configuration file. Defaults to "config.yaml"
        
    Returns:
        Dict[Any, Any]: Dictionary containing the parsed YAML content
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If the YAML file is invalid or cannot be parsed
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            
        if config is None:
            return {}
            
        return config
        
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {e}")