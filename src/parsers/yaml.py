# Built-in Libraries
import logging
from typing import TYPE_CHECKING

# Third Party Libraries
from ruamel.yaml import YAML

# Local Libraries
# N/A

# Type Checking
if TYPE_CHECKING:
	from pathlib import Path

# ==============================================================================
# Initializers
# ==============================================================================
logger = logging.getLogger(__name__)
yaml = YAML(typ="safe")


# ==============================================================================
# Shared Helpers
# ==============================================================================
def load(file: "Path") -> dict:
	data = {}

	try:
		with file.open() as f:
			data = yaml.load(f)

			if logger.isEnabledFor(logging.DEBUG):
				logger.debug(data)
	except Exception as e:
		logger.exception(e)
		raise

	return data
