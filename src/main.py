# Built-in Libraries
import argparse
import logging
import sys
from enum import StrEnum

# Third Party Libraries
# N/A

# Local Libraries
from config import Settings
# import cli
# import gui

class Mode(StrEnum):
	cli = "cli"
	gui = "gui"

	def __repr__(self):
		return self.name

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("--mode", choices=list(Mode))
	return parser.parse_args()

def main():
	if len(sys.argv) > 1:
		args = parse_args()
		mode = args.mode
	else:
		mode = "gui"

	print(mode)
	match mode:
		case "gui":
			print(1) # gui()
		case "cli":
			print(2) # cli()
		case _:
			raise

# ------------------------------------------------------------------------------
if __name__ == "__main__":
	from generators.tickets import generate_tickets
	generate_tickets(1)
	# print(Settings.ticket)
	# print(list(Mode))
	# print(sys.argv)
	# sys.argv.append("--mode=gui")
	# main()
