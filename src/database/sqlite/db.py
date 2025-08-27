# Built-in Libraries
# N/A

# Third Party Libraries
# N/A

# Local Libraries
from database.sqlite import con, cur

# ------------------------------------------------------------------------------
def lookup_code(code):
	try:
		return queryOneDict("""
			SELECT *
			FROM barcodes
			WHERE code = ?;
		""", (code,))
	except Exception as e:
		return {"error": str(e)}


# ------------------------------------------------------------------------------
def insert(codes):
	cur.executemany("""
		INSERT INTO barcodes (code)
		VALUES (?);
	""", [(code,) for code in codes])


# ------------------------------------------------------------------------------
def update(code, used=0):
	if used:
		return

	cur.execute("""
		UPDATE barcodes
		SET used = 1
		WHERE code = ?;
	""", (code,))


# ------------------------------------------------------------------------------
def queryValList(sql, vals=None):
	try:
		results = cur.execute(sql, vals or tuple())
		return [r[0] for r in cur.fetchall()]
	except Exception:
		raise


# ------------------------------------------------------------------------------
def queryOneDict(sql, vals=None):
	try:
		results = cur.execute(sql, vals or tuple())
		keys = [r[0] for r in results.description]
		vals = results.fetchall()[0]
		return {k: v for k, v in zip(keys, vals)}
	except Exception:
		return {}
