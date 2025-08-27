# Built-in Libraries
import importlib

# Third Party Libraries
# N/A

# Local Libraries
from config import Settings


# ==============================================================================
def get_database_module(driver):
	return importlib.import_module(f"database.{driver}.db")


db = get_database_module(Settings.database.driver)
