# -*- mode: python ; coding: utf-8 -*-

# Built-in Libraries
import shutil
import tomllib
from pathlib import Path

# Third Party Libraries
import pyinstaller_versionfile

# Local Libraries
# N/A

# ==============================================================================
# Globals
# ==============================================================================
ROOT = Path(SPECPATH)

# ==============================================================================
# Version File
# ==============================================================================
VERSIONFILE = ROOT / "versionfile.txt"

with (ROOT / "pyproject.toml").open("rb") as f:
	toml = tomllib.load(f)

project = toml["project"]

pyinstaller_versionfile.create_versionfile(
	output_file=VERSIONFILE.name,
	version=project["version"],
	company_name="Jared Hinze",
	file_description=project["description"],
	internal_name=project["name"],
	legal_copyright=project["license"],
	original_filename=f'{project["name"]}.exe',
	product_name=project["name"],
	# https://learn.microsoft.com/en-us/windows/win32/menurc/varfileinfo-block
	translations=[int("0x0409", 16), 1200],
)

if VERSIONFILE.exists():
	print(f"Created: {VERSIONFILE}")
else:
	import sys
	print(f"Failed to create {VERSIONFILE}")
	sys.exit(1)

# ==============================================================================
# Spec
# ==============================================================================
a = Analysis(
    ["src/main.py"],
    pathex=[],
    binaries=[],
    datas=[("src/assets", "assets")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

e = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=project["name"],
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["src/assets/app.ico"],
    version=VERSIONFILE.name,
)

# ==============================================================================
# Custom carry over of configuration files
# ==============================================================================
print("Running Custom Build Extension")
distdir = ROOT / "dist"

log = distdir / "logs/report.log"
log.parent.mkdir(exist_ok=True)
log.touch()
