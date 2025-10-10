# Built-in Libraries
import json
import logging
import string
from itertools import product
from pathlib import Path

# Third Party Libraries
from hypothesis import given, strategies as st
from pytest import fixture, raises

# Local Libraries
from generators import tickets


# ==============================================================================
# Fixtures
# ==============================================================================


# ==============================================================================
# Tests
# ==============================================================================
@given(
	chars=st.text(alphabet=string.printable, min_size=1),
	length=st.integers(min_value=5, max_value=10),
)
def test_generate_code_with_open_exclusion_window(chars, length):
	"""Generate unique string given a character set, length, and no exclusions"""
	tickets.generate_code(chars, length, set())


# ------------------------------------------------------------------------------
@given(length=st.integers(min_value=8, max_value=13))
def test_generate_code_with_tight_exclusion_window(length):
	"""Generate unique string given a character set, length, and many exclusions"""
	chars = ''.join(chr(ord('a') + i) for i in range(length))
	excludes = {''.join(s) for s in product(chars, repeat=length)}
	excludes.pop() # create a single opening in the set

	tickets.generate_code(chars, length, excludes)


# ------------------------------------------------------------------------------
@given(
	chars=st.text(min_size=1, max_size=13),
	length=st.integers(min_value=8, max_value=13)
)
def test_generate_code_with_full_exclusion_window(chars, length):
	"""Crash when there's no way to generate a new code"""
	with raises(ValueError, match="Code generation impossible"):
		excludes = {
			''.join(s)
			for i in range(1, length + 1)
			for s in product(chars, repeat=i)
		}
		tickets.generate_code(chars, length, excludes)
