import json
import os
import sys
import logging
from types import SimpleNamespace

try:
    import jsonschema
except ImportError:
    print("Error: jsonschema module not found. Please install it with 'pip install jsonschema'")
    sys.exit(1)

class ConfigHandler:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.realpath(__file__))
        self.config_file = os.path.join(self.base_path, 'config.json')
        self.schema_file = os.path.join(self.base_path, 'schema.json')
        self.config = None
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            print(f"Config file not found: {self.config_file}")
            sys.exit(1)
        
        if not os.path.exists(self.schema_file):
            print(f"Schema file not found: {self.schema_file}")
            sys.exit(1)

        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            with open(self.schema_file, 'r') as f:
                schema_data = json.load(f)
            
            # Validate against schema
            jsonschema.validate(instance=config_data, schema=schema_data)
            
            # Merge with defaults
            full_config = self._merge_defaults(config_data)
            
            # Convert to object for dot notation access
            self.config = self._to_object(full_config)
            
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            sys.exit(1)
        except jsonschema.ValidationError as e:
            print(f"Configuration validation failed: {e.message}")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            sys.exit(1)

    def _merge_defaults(self, config):
        # Defaults based on schema.json descriptions
        defaults = {
            "mbus": {"port": "/dev/ttyS0", "baudRate": 2400},
            "logging": {
                "console": {"enabled": True, "format": "raw", "level": "INFO"},
                "file": {"enabled": False, "format": "json", "path": "", "level": "INFO"},
                "loki": {"enabled": False, "url": "", "level": "INFO"}
            },
            "mqtt": {
                "enabled": False,
                "brokerPort": 1883,
                "authentication": {"isAuthenticated": False, "username": "", "password": ""},
                "mqttApiVersion": 1,
                "mqttPrefix": "smartmeter"
            },
            "influxdb": {
                "enabled": False,
                "serverPort": 8086,
                "authentication": {"isAuthenticated": False, "username": "", "password": ""},
                "database": "smartmeter",
                "organization": "smartmeter",
                "version": 2,
                "sendMetrics": False,
                "sendValues": True
            },
            "prometheus": {
                "enabled": False,
                "port": 8000,
                "exposeMetrics": True,
                "exposeValues": False
            }
        }
        return self._deep_merge(defaults, config)

    def _deep_merge(self, source, destination):
        for key, value in destination.items():
            if isinstance(value, dict):
                node = source.setdefault(key, {})
                self._deep_merge(node, value)
            else:
                source[key] = value
        return source

    def _to_object(self, data):
        if isinstance(data, dict):
            return SimpleNamespace(**{k: self._to_object(v) for k, v in data.items()})
        elif isinstance(data, list):
            return [self._to_object(v) for v in data]
        return data

    def get_config(self):
        return self.config

def get_configuration():
    return ConfigHandler().get_config()