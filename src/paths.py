# Built-in Libraries
import sys
from pathlib import Path

# Third Party Libraries
# N/A

# Local Libraries
# N/A

# ==============================================================================
# Helpers
# ==============================================================================
def ensure_directory(*paths):
	p = Path(*paths)
	if not p.is_dir():
		p.mkdir(exist_ok=True, parents=True)
	return p

# ------------------------------------------------------------------------------
def ensure_file(base_dir, file):
	p = ensure_directory(base_dir)
	p /= file
	if not p.is_file():
		p.touch(exist_ok=True)
	return p

# ==============================================================================
# Paths
# ==============================================================================
if getattr(sys, "frozen", False):
    BASEDIR = Path(sys.executable).parent
    DIR_ASSETS = Path(sys._MEIPASS) / "assets"
else:
    BASEDIR = Path(__file__).parent
    DIR_ASSETS = BASEDIR / "assets"

# Assets
DIR_IMAGES = ensure_directory(DIR_ASSETS, "images")
DIR_SOUNDS = ensure_directory(DIR_ASSETS, "sounds")

# Outputs
DIR_OUTPUTS = BASEDIR / "outputs"
DIR_SHEETS = ensure_directory(DIR_OUTPUTS / "sheets")
DIR_TICKETS = ensure_directory(DIR_OUTPUTS / "tickets")
