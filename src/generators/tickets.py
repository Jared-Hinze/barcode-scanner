# Built-in Libraries
import math
import uuid

# Third Party Libraries
import barcode
import rstr
from barcode.writer import ImageWriter
from PIL import Image

# Local Libraries
from config import Settings
from database import db
from paths import DIR_IMAGES, DIR_TICKETS

# ==============================================================================
# Settings
# ==============================================================================
Barcode = Settings.barcode
Ticket = Settings.ticket


# ==============================================================================
def generate_code(chars, length, excludes):
	while (code := rstr.xeger(rf"[{chars}]{{{length}}}")) in excludes:
		continue
	return code


# ------------------------------------------------------------------------------
def create_barcode(fmt, code, filename):
	module = barcode.get_barcode_class(fmt)
	return module(code, writer=ImageWriter()).save(
		filename=DIR_TICKETS / str(filename),
		options=Barcode.save_options,
	)


# ------------------------------------------------------------------------------
def generate_tickets(n):
	if n < 1:
		return

	barcode_fmt = Barcode.format.lower()
	if barcode_fmt not in barcode.PROVIDED_BARCODES:
		raise ValueError(
			f'barcode.format="{barcode_fmt}" is not supported. '
			f'Please use one of the following: {barcode.PROVIDED_BARCODES}'
		)

	chars = Barcode.chars
	length = Barcode.length

	if getattr(Ticket, "header", ''):
		header_img = Image.open(Ticket.header)
	else:
		header_img = Image.open(DIR_IMAGES / "header.png")

	header_x, header_y = header_img.size
	header_shift_x = barcode_shift_x = None
	barcode_x = barcode_y = scalar = 0
	ticket_size = None

	db_codes = set(db.queryValList("SELECT code FROM barcodes;"))
	new_codes = set()

	# Generate the barcodes
	for i in range(n):
		code = generate_code(chars, length, db_codes | new_codes)
		barcode_path = create_barcode(barcode_fmt, code, uuid.uuid4())
		try:
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
		except Exception as e:
			print(f"Error: {e}")
			continue
		else:
			new_codes.add(code)

	# Sync database
	db.insert(new_codes)
