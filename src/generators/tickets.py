# Built-in Libraries
import math
import random
import string
import uuid

# Third Party Libraries
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image

# Local Libraries
from database.sqlite import db
from paths import DIR_IMAGES, DIR_TICKETS

# ==============================================================================
# Helpers
# ==============================================================================
def generate_code(character_set, excludes):
	while (code := ''.join(random.choices(character_set, k=12))) in excludes:
		continue
	return code

# ------------------------------------------------------------------------------
def create_barcode(code, filename):
	return Code128(code, writer=ImageWriter()).save(
		filename=DIR_TICKETS / str(filename),
		options={
			"module_height": 5,
			"module_width": 0.2,
			"text_distance": 3,
			"font_size": 5,
		},
	)

# ==============================================================================
# Functions
# ==============================================================================
def generate_tickets(n):
	if n < 1:
		return

	character_set = string.digits + string.ascii_uppercase
	db_codes = set(db.queryValList("SELECT code FROM barcodes;"))
	new_codes = set()

	header_img = Image.open(DIR_IMAGES / "header.png")
	header_x, header_y = header_img.size

	header_shift_x = barcode_shift_x = None
	barcode_x = barcode_y = scalar = None
	ticket_size = None

	# Generate the barcodes
	for i in range(n):
		code = generate_code(character_set, db_codes | new_codes)
		barcode_path = create_barcode(code, uuid.uuid4())
		try:
			barcode_img = Image.open(barcode_path)

			# Scale the barcode to fit as desired for the sheets later
			if not scalar:
				barcode_x, barcode_y = barcode_img.size
				scalar = 400 / barcode_x
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
			ticket_img = Image.new("RGB", size=ticket_size, color=0xFFFFFF)
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


# ==============================================================================
if __name__ == "__main__":
	print("Starting...")
	generate_tickets(1)
	print("Finished")
