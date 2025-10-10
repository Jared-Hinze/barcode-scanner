# Built-in Libraries
import importlib

# Third Party Libraries
# N/A

# Local Libraries
from config import Settings


# ==============================================================================
def get_database_module(module_path):
	return importlib.import_module(module_path)


driver = Settings.database.driver

module = get_database_module(f"database.{driver}")
module.initialize()

db = get_database_module(f"database.{driver}.db")
