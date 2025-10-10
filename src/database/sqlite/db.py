# Built-in Libraries
from collections.abc import Iterable
import sqlite3

# Third Party Libraries
# N/A

# Local Libraries
from database import sqlite as db


# ------------------------------------------------------------------------------
def execute(sql, vals=None) -> sqlite3.Cursor:
	return db.cur.execute(sql, vals or tuple())


# ------------------------------------------------------------------------------
def executemany(sql, vals=None) -> sqlite3.Cursor:
	return db.cur.executemany(sql, vals or tuple())


# ------------------------------------------------------------------------------
def insert(codes: Iterable[str]) -> sqlite3.Cursor:
	if not hasattr(codes, "__iter__"):
		raise TypeError(f'Expected iterable. Got "{type(codes)}".')

	if isinstance(codes, str):
		codes = (codes,)

	return executemany(
		""" INSERT INTO barcodes (code)
			VALUES (?);
		""",
		[(code,) for code in codes],
	)


# ------------------------------------------------------------------------------
def update(code: str) -> sqlite3.Cursor:
	if not isinstance(code, str):
		raise TypeError(f"Expected string. Got '{type(code)}'.")

	return execute(
		""" UPDATE barcodes
			SET used = 1
			WHERE code = ?;
		""",
		(code,),
	)


# ------------------------------------------------------------------------------
def queryOneVal(sql, vals=None, default=None):
	cursor = execute(sql, vals)

	if len(cursor.description) > 1:
		raise ValueError("Query returned multiple columns. Expected 1 column.")

	recs = cursor.fetchall()
	if len(recs) > 1:
		raise ValueError("Query returned multiple rows. Expected 1 row.")

	if len(recs) == 1:
		return recs[0][0]

	return default


# ------------------------------------------------------------------------------
def queryValList(sql, vals=None, default=None) -> list:
	cursor = execute(sql, vals)

	if len(cursor.description) > 1:
		raise ValueError("Query returned multiple columns. Expected 1 column.")

	if recs := cursor.fetchall():
		return [rec[0] for rec in recs]

	return default or []


# ------------------------------------------------------------------------------
def queryOneDict(sql, vals=None, default=None) -> dict:
	cursor = execute(sql, vals)

	recs = cursor.fetchall()
	if len(recs) > 1:
		raise ValueError("Query returned multiple rows. Expected 1 row.")

	if recs:
		keys = [r[0] for r in cursor.description]
		return {k: v for k, v in zip(keys, recs[0])}

	return default or {}


# ------------------------------------------------------------------------------
def lookup_code(code) -> dict:
	try:
		return queryOneDict(
			""" SELECT *
				FROM barcodes
				WHERE code = ?;
			""",
			vals=(code,),
		)
	except Exception as e:
		return {"error": str(e)}
