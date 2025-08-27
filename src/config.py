# Built-in Libraries
import logging.config

# Third Party Libraries
# N/A

# Local Libraries
from parsers import yaml
from paths import DIR_CONFIGS, ensure_file

# ==============================================================================
# Constants
# ==============================================================================
FILE_LOGGING_CONFIG = ensure_file(DIR_CONFIGS, "logging_config.yaml")
FILE_SETTINGS = ensure_file(DIR_CONFIGS, "settings.yaml")

# ==============================================================================
# Logging
# ==============================================================================
if not logging._handlers:
	logging.config.dictConfig(yaml.load(FILE_LOGGING_CONFIG))


# ==============================================================================
# Helper Class
# ==============================================================================
# Convert YAML dict to obj.key1.key2.list[i].key3...
class AttrDict(dict):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.__dict__ = self

	@classmethod
	def from_file(cls, file):
		return cls.from_map(yaml.load(file))

	@classmethod
	def from_map(cls, data):
		if isinstance(data, dict):
			return cls({k.replace('-', '_'): cls.from_map(v) for k, v in data.items()})
		elif isinstance(data, list):
			return [cls.from_map(v) if isinstance(v, dict) else v for v in data]
		else:
			return data


# ==============================================================================
# Cached
# ==============================================================================
Settings = AttrDict.from_file(FILE_SETTINGS)
