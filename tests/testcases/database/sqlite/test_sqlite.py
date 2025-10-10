# Built-in Libraries
import json
import logging
import sqlite3
import string
import tempfile
import uuid
from pathlib import Path
from unittest import mock

# Third Party Libraries
from hypothesis import given, strategies as st
from pytest import fixture, raises

# Local Libraries
from database import sqlite
from database.sqlite import db
from helpers import has_message
from paths import ensure_file


# ==============================================================================
# Helpers
# ==============================================================================
def unique_code():
	return str(uuid.uuid4())


# ==============================================================================
# Fixtures
# ==============================================================================
@fixture(scope="session", autouse=True)
def db_info():
	with tempfile.TemporaryDirectory() as tmp_dir:
		# setup
		sqlite.initialize(ensure_file(tmp_dir, "test.db"))

		yield type("DbInfo", (), {"connection": sqlite.con, "cursor": sqlite.cur})

		# teardown
		sqlite.cur.close()
		sqlite.con.close()


# ------------------------------------------------------------------------------
@fixture(scope="function", autouse=True)
def clean_tables(db_info):
	cur = db_info.cursor

	# Find tables that could have changed
	cur.execute("""
		SELECT name
		FROM sqlite_master
		WHERE type='table'
		  AND name NOT LIKE 'sqlite_%';
	""")

	# Nuke all table contents
	for (table_name,) in cur.fetchall():
		cur.execute(f"DELETE FROM {table_name};")

	try:
		# Reset any auto-increment sequences
		cur.execute("DELETE FROM sqlite_sequence;")
	except sqlite3.OperationalError:
		# Fails if nothing uses AUTOINCREMENT
		pass

	db_info.connection.commit()


# ==============================================================================
# Tests
# ==============================================================================
def test_execute_returns_cursor():
	"""Ensure db.execute returns a cursor object"""
	assert isinstance(db.execute("SELECT 1;"), sqlite3.Cursor)


# ------------------------------------------------------------------------------
def test_execute_bad_sql():
	"""Crash if an invalid SQL string is passed in"""
	with raises(sqlite3.OperationalError):
		db.execute("foo")


# ------------------------------------------------------------------------------
def test_execute_bad_vals():
	"""Crash if sqlite3 cannot automatically bind supplied vals"""
	with raises(sqlite3.ProgrammingError):
		db.execute("SELECT ?", (object(),))


# ------------------------------------------------------------------------------
def test_execute_with_val_sequence():
	"""Properly handle argument substitution for iterables"""
	db.execute("SELECT ?", (1,))


# ------------------------------------------------------------------------------
def test_execute_with_val_mapping():
	"""Properly handle argument substitution for mappings"""
	db.execute("SELECT :num", {"num": 1})


# ------------------------------------------------------------------------------
def test_executemany_non_dml_query():
	"""Sqlite3 crashes when executemany is used for non-DML queries"""
	with raises(sqlite3.ProgrammingError):
		db.executemany("SELECT 1;")


# ------------------------------------------------------------------------------
def test_executemany_returns_cursor():
	"""Ensure db.executemany returns a cursor object"""
	result = db.executemany("""
		UPDATE barcodes
		SET used = 1
		WHERE code = 'foo';
	""")
	assert isinstance(result, sqlite3.Cursor)


# ------------------------------------------------------------------------------
def test_executemany_bad_sql():
	"""Crash if an invalid SQL string is passed in"""
	with raises(sqlite3.OperationalError):
		db.executemany("foo")


# ------------------------------------------------------------------------------
def test_executemany_bad_vals():
	"""Crash if sqlite3 cannot automatically bind supplied vals"""
	with raises(sqlite3.ProgrammingError):
		db.executemany("SELECT ?", (object(),))


# ------------------------------------------------------------------------------
def test_executemany_with_val_sequence():
	"""Properly handle argument substitution for iterables"""
	db.executemany(
		""" UPDATE barcodes
			SET used = 1
			WHERE code = ?;
		""",
		[("foo",)],
	)


# ------------------------------------------------------------------------------
def test_executemany_with_val_mapping():
	"""Properly handle argument substitution for mappings"""
	db.executemany(
		""" UPDATE barcodes
			SET used = 1
			WHERE code = :code;
		""",
		[{"code": "foo"}],
	)


# ------------------------------------------------------------------------------
def test_insert_non_iterable_errors():
	"""Raise TypeError if passing in a non-iterable"""
	with raises(TypeError):
		db.insert(object())


# ------------------------------------------------------------------------------
def test_insert_bad_data_type():
	"""Iterables with non-string elements should crash."""
	with raises(sqlite3.DatabaseError):
		db.insert((object() for _ in range(1)))


# ------------------------------------------------------------------------------
def test_insert_iterable_returns_cursor():
	"""Ensure db.insert returns a cursor object"""
	assert isinstance(db.insert([]), sqlite3.Cursor)


# ------------------------------------------------------------------------------
def test_insert_empty_iterable():
	"""Do nothing if empty iterable provided"""
	assert db.insert([]).rowcount == 0


# ------------------------------------------------------------------------------
def test_insert_single_item():
	"""A single string should be added. Careful of listify'ing it."""
	code = unique_code()
	assert db.insert(code).rowcount == 1
	assert db.lookup_code(code)


# ------------------------------------------------------------------------------
@given(length=st.integers(min_value=2, max_value=5))
def test_insert_many_uniques(length):
	"""Multiple unique codes should be added to database successfully"""
	codes = [unique_code() for _ in range(length)]
	assert db.insert(codes).rowcount == length
	assert db.lookup_code(codes[0])


# ------------------------------------------------------------------------------
def test_insert_many_with_duplicates():
	"""Duplicate codes should crash"""
	code = unique_code()
	with raises(sqlite3.IntegrityError):
		db.insert([code, code])


# ------------------------------------------------------------------------------
def test_update_bad_data_type():
	"""Ensure TypeError if the code isn't a string"""
	with raises(TypeError):
		db.update(object())


# ------------------------------------------------------------------------------
def test_update_returns_cursor():
	"""Ensure db.update returns a cursor object"""
	assert isinstance(db.update("foo"), sqlite3.Cursor)


# ------------------------------------------------------------------------------
def test_update_non_existing_code():
	"""Do nothing if the code doesn't exist"""
	assert db.update("foo").rowcount == 0


# ------------------------------------------------------------------------------
def test_update_existing_unused_code():
	"""Set used=1 for existing codes"""
	code = unique_code()
	db.insert(code)

	before = db.lookup_code(code)
	db.update(code)
	after = db.lookup_code(code)

	assert before["code"] == after["code"]
	assert before["used"] != after["used"]


# ------------------------------------------------------------------------------
def test_update_existing_used_code():
	"""No change for used existing codes"""
	code = unique_code()
	db.insert(code)
	db.update(code)

	before = db.lookup_code(code)
	db.update(code)
	after = db.lookup_code(code)

	assert before["used"] == after["used"]


# ------------------------------------------------------------------------------
def test_queryOneVal_bad_sql():
	"""Error if bad sql is provided"""
	with raises(sqlite3.OperationalError):
		assert db.queryOneVal("foo")


# ------------------------------------------------------------------------------
def test_queryOneVal_multiple_columns():
	"""Error if queryOneVal returns multiple columns"""
	with raises(ValueError, match="Query returned multiple columns"):
		assert db.queryOneVal("SELECT 2, 3;") == 2


# ------------------------------------------------------------------------------
def test_queryOneVal_multiple_rows():
	"""Error if queryOneVal returns multiple rows"""
	with raises(ValueError, match="Query returned multiple rows"):
		assert db.queryOneVal("SELECT 1 UNION SELECT 2;")


# ------------------------------------------------------------------------------
def test_queryOneVal_single_row():
	"""Ensure queryOneVal returns the one value"""
	assert db.queryOneVal("SELECT 2;") == 2


# ------------------------------------------------------------------------------
def test_queryOneVal_default_when_no_rows():
	"""Return the default when no rows are found"""
	default = "foo"
	assert db.queryOneVal("SELECT 1 WHERE FALSE;", default=default) == default


# ------------------------------------------------------------------------------
def test_queryValList_multiple_columns():
	"""Error if queryValList returns multiple columns"""
	with raises(ValueError, match="Query returned multiple columns"):
		assert db.queryOneVal("SELECT 2, 3;") == 2


# ------------------------------------------------------------------------------
def test_queryValList_default_when_no_rows():
	"""Return the default when no rows are found"""
	default = "foo"
	assert db.queryValList("SELECT 1 WHERE FALSE;", default=default) == default


# ------------------------------------------------------------------------------
def test_queryValList_multiple_rows():
	"""Ensure queryValList returns the list of values"""
	assert db.queryValList("SELECT 1 UNION SELECT 2;") == [1, 2]


# ------------------------------------------------------------------------------
def test_queryOneDict_multiple_rows():
	"""Error if queryOneDict returns multiple rows"""
	with raises(ValueError, match="Query returned multiple rows"):
		assert db.queryOneDict("""
			SELECT 1 AS num
			UNION
			SELECT 2 AS num;
		""")


# ------------------------------------------------------------------------------
def test_queryOneDict_single_row():
	"""Ensure dict return with valid query"""
	rec = db.queryOneDict("SELECT 1 AS n1, 2 AS n2;")
	assert rec == {"n1": 1, "n2": 2}


# ------------------------------------------------------------------------------
def test_queryOneDict_default_when_no_rows():
	"""Return the default when no rows are found"""
	default = {"foo": None}
	assert db.queryOneDict("SELECT 1 WHERE FALSE;", default=default) == default


# ------------------------------------------------------------------------------
def test_lookup_code_error():
	"""If an error occurs we should get a dict with information back"""
	result = db.lookup_code(object())
	assert isinstance(result, dict)
	assert "error" in result
	assert result["error"]


# ------------------------------------------------------------------------------
def test_lookup_code_missing():
	"""Return an empty dict if the code isn't found without error"""
	assert db.lookup_code('') == {}


# ------------------------------------------------------------------------------
def test_lookup_code_existing():
	"""Return a record as a dict if the code is found"""
	code = unique_code()
	db.insert(code)

	result = db.lookup_code(code)
	assert result
	assert isinstance(result, dict)
