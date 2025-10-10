# Built-in Libraries
import json
import logging
from pathlib import Path

# Third Party Libraries
from hypothesis import given, strategies as st
from pytest import fixture, raises

# Local Libraries
import database
from helpers import has_message


# ==============================================================================
# Tests
# ==============================================================================
def test_get_database_module_bad_or_missing_driver():
	"""Bad or missing drivers should return crash"""
	with raises(ModuleNotFoundError):
		assert database.get_database_module("foo.bar")


# ------------------------------------------------------------------------------
@given(driver=st.sampled_from(["sqlite"]))
def test_get_database_module_existing_driver(driver):
	"""Existing good drivers should return back their module"""
	assert database.get_database_module(driver)
