# Built-in Libraries
import json
import logging
from pathlib import Path

# Third Party Libraries
from pytest import fixture, raises

# Local Libraries
from parsers import yaml
from helpers import has_message


# ==============================================================================
# Fixtures
# ==============================================================================
@fixture(scope="function")
def tmp_yaml(tmp_path: Path):
	def factory(model: dict):
		tmp_file = tmp_path / "foo.yaml"
		with tmp_file.open('w') as f:
			f.write(json.dumps(model).replace('"', ''))
		return tmp_file

	return factory


# ==============================================================================
# Tests
# ==============================================================================
def test_load_bad_or_missing_file(caplog):
	"""Bad or missing files should return an empty dict"""
	caplog.set_level(logging.ERROR)
	with raises(FileNotFoundError, match="No such file or directory"):
		assert yaml.load(Path("foo.yaml")) == {}


# ------------------------------------------------------------------------------
def test_load_debug_enabled(caplog, tmp_yaml):
	"""We should see data when debug is enabled"""
	caplog.set_level(logging.DEBUG)

	model = {"test": 1}
	tmp_file = tmp_yaml(model)

	yaml.load(tmp_file)

	assert has_message(caplog, str(model), predicate=str.__eq__)


# ------------------------------------------------------------------------------
def test_load_existing_file(tmp_yaml):
	"""Existing good YAML files should return back their data structure"""
	model = {"test": 1}
	tmp_file = tmp_yaml(model)

	assert yaml.load(tmp_file) == model
