# Built-in Libraries
import logging
import math
import re
import string
import uuid

# Third Party Libraries
import barcode
from barcode.writer import ImageWriter
from PIL import Image

# Local Libraries
from config import Settings
from database import db
from generators.code_generator import CodeGenerator
from paths import DIR_IMAGES, DIR_TICKETS

# ==============================================================================
# Initializers
# ==============================================================================
logger = logging.getLogger(__name__)

# ==============================================================================
# Settings
# ==============================================================================
Barcode = Settings.barcode
Ticket = Settings.ticket


# ==============================================================================
def create_charset(chars):
	if not chars:
		return ''

	S = set()
	for part in re.findall(r"\[?(\\[dw]|.-.|.(?!-.))\]?", chars):
		if len(part) == 3:
			lo, hi = part.split('-')

			tests = (str.islower, str.isupper, str.isdigit)
			if not any(test(lo) and test(hi) for test in tests):
				raise ValueError(f"Error: [{lo}-{hi}] impossible")
			if lo > hi:
				raise ValueError(f"Error: '{lo}' > '{hi}' impossible")

			S.update(chr(i) for i in range(ord(lo), ord(hi) + 1))
		elif part == r"\w":
			S.update(f"{string.ascii_letters}{string.digits}_")
		elif part == r"\d":
			S.update(string.digits)
		else:
			S.add(part)

	return ''.join(S)


# ------------------------------------------------------------------------------
def create_barcode(fmt):
	module = barcode.get_barcode_class(fmt)

	def writer(code, filename):
		return module(code, writer=ImageWriter()).save(
			filename=DIR_TICKETS / str(filename),
			options=Barcode.save_options,
		)

	return writer


# ------------------------------------------------------------------------------
def generate_tickets(n):
	if n < 1:
		return

	barcode_fmt = Barcode.format.lower()
	if barcode_fmt not in barcode.PROVIDED_BARCODES:
		raise ValueError(
			f'barcode.format="{barcode_fmt}" is not supported. '
			f'Use one of the following: {barcode.PROVIDED_BARCODES}'
		)

	chars = create_charset(Barcode.chars)
	length = Barcode.length

	if getattr(Ticket, "header", ''):
		header_img = Image.open(Ticket.header)
	else:
		header_img = Image.open(DIR_IMAGES / "header.png")

	header_x, header_y = header_img.size
	header_shift_x = barcode_shift_x = None
	barcode_x = barcode_y = scalar = 0
	ticket_size = None

	db_codes = db.queryValList("SELECT DISTINCT code FROM barcodes;")

	# Generate the codes
	G = CodeGenerator(barcode_fmt, alphabet=chars, length=length, used=db_codes)
	codes = G.generate(n)

	# Generate the barcodes
	writer = create_barcode(barcode_fmt)
	for code in codes.copy():
		try:
			barcode_path = writer(code, uuid.uuid4())
			barcode_img = Image.open(barcode_path)

			# Scale the barcode to fit as desired for the sheets later
			if scalar == 0:
				barcode_x, barcode_y = barcode_img.size
				scalar = Barcode.scalar / barcode_x
				barcode_x = math.floor(barcode_x * scalar)
				barcode_y = math.floor(barcode_y * scalar)

			barcode_img = barcode_img.resize((barcode_x, barcode_y))

			# Determine any left/right shifting required
			if header_shift_x is None:
				header_shift_x = (barcode_x - header_x) // 2 if barcode_x > header_x else 0
			if barcode_shift_x is None:
				barcode_shift_x = (header_x - barcode_x) // 2 if header_x > barcode_x else 0

			# Determine final dimensions
			if ticket_size is None:
				ticket_size = (max((header_x, barcode_x)), header_y + barcode_y)

			# Make ticket
			ticket_img = Image.new("RGB", size=ticket_size, color=Ticket.background_color)
			ticket_img.paste(header_img, (header_shift_x, 0))
			ticket_img.paste(barcode_img, (barcode_shift_x, header_y))
			ticket_img.save(barcode_path, "PNG")

			logger.debug(f'Generated code: "{code}"')
		except Exception as e:
			print(f"Error: {e}")
			codes.remove(code)

	# Sync database
	db.insert(codes)

if __name__ == "__main__":
	db.execute("DELETE FROM barcodes;")
	generate_tickets(3)
