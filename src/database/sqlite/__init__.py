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
con = sqlite3.connect(
	database=ensure_file(Path(__file__).parent, "barcodes.db"),
	autocommit=True, # won't have complex transactions
)
cur = con.cursor()

# ==============================================================================
# Initialize Database
# ==============================================================================
cur.execute("""
	CREATE TABLE IF NOT EXISTS barcodes (
		code TEXT    UNIQUE,   -- barcode value
		used INTEGER DEFAULT 0 -- boolean [0, 1]
	);
""")

