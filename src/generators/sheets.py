# Built-in Libraries
import uuid
from collections import namedtuple
from itertools import product
from PIL import Image, ImageOps

# Third Party Libraries
# N/A

# Local Libraries
from config import Settings
from paths import DIR_SHEETS, DIR_TICKETS

# ==============================================================================
# Settings
# ==============================================================================
Sheet = Settings.sheet

# ==============================================================================
# Structs
# ==============================================================================
Border = namedtuple("Border", ["left", "top", "right", "bottom"])  # ImageOps order...
Layout = namedtuple("Layout", ["rows", "columns"])


# ==============================================================================
def generate_sheets():
	border = Border(*Sheet.border)
	border_color = Sheet.border_color

	images = [
		ImageOps.expand(Image.open(file), border=border, fill=border_color)
		for file in DIR_TICKETS.glob("*.png")
	]  # fmt: skip
	if not images:
		return

	size = images[0].size
	total_images = len(images)

	layout = Layout(Sheet.rows, Sheet.columns)
	step = layout.rows * layout.columns
	for i in range(0, total_images, step):
		generate_sheet(images[i : i + step], layout, size, border)


# ------------------------------------------------------------------------------
def generate_sheet(images, layout, size, border):
	image_count = len(images)
	width, height = size

	full_image_size = (
		layout.columns * (width + border.left + border.right),
		layout.rows * (height + border.top + border.bottom),
	)
	background_color = Sheet.background_color
	image = Image.new("RGB", size=full_image_size, color=background_color)

	for i, (row, col) in enumerate(product(*map(range, layout))):
		if i == image_count:
			break

		offset = (
			col * (width + border.left + border.right),
			row * (height + border.top + border.bottom),
		)
		image.paste(images[i], tuple(offset))

	image.save(DIR_SHEETS / f"{uuid.uuid4()}.png", "PNG")
