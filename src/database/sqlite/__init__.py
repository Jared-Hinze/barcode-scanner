# Built-in Libraries
import sqlite3
from pathlib import Path

# Third Party Libraries
# N/A

# Local Libraries
from paths import ensure_file

# ==============================================================================
# Globals
# ==============================================================================
con = cur = None


# ==============================================================================
# Initialize Database
# ==============================================================================
def connect(db_path, autocommit=True, **kwargs):
	# Using autocommit=True default since we won't have complex transactions
	return sqlite3.connect(database=db_path, autocommit=autocommit)


# ------------------------------------------------------------------------------
def create_schema():
	cur.execute("""
		CREATE TABLE IF NOT EXISTS barcodes (
			code TEXT    UNIQUE,   -- barcode value
			used INTEGER DEFAULT 0 -- boolean [0, 1]
		);
	""")


# ------------------------------------------------------------------------------
def initialize(db_path=ensure_file(Path(__file__).parent, "barcodes.db"), **kwargs):
	global con, cur
	con = connect(db_path, **kwargs)
	cur = con.cursor()
	create_schema()
