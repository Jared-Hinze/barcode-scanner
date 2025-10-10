# Built-in Libraries
import secrets
import string
from itertools import pairwise
from typing import TYPE_CHECKING

# Third Party Libraries
import barcode

# Local Libraries
from config import Settings

if TYPE_CHECKING:
	from barcode.base import Barcode
	from collections.abc import Iterator

# ==============================================================================
class CodeGenerator:
	def __init__(self, fmt, *, alphabet='', length=0, used=None):
		""" fmt            : The barcode format to base the generator off of.
			alphabet: Must be a subset of the expected alphabet.
			length  : The length of the barcode.
			used           : An iterable of unique used barcodes.
		"""
		if not isinstance(fmt, str):
			raise TypeError("Barcode format must be a string.")

		self.chars = self.get_alphabet(fmt, alphabet)
		self.length = self.get_length(fmt, length)

		self._used = set(map(self._to_code, used)) if used else set()

		self._base = len(self.chars)
		self._limit = self._base ** self.length
		self._remaining = self._limit - len(self._used)

		self._sectors = self._get_sectors()

	# --------------------------------------------------------------------------
	def __iter__(self) -> "Iterator":
		"""Allow users to treat the class as a iterator"""
		return self

	# --------------------------------------------------------------------------
	def __next__(self) -> str:
		"""Allow users to treat the class as a generator"""
		if self._remaining == 0:
			raise StopIteration

		return self.generate().pop()

	# --------------------------------------------------------------------------
	@staticmethod
	def get_alphabet(fmt, alphabet='') -> str:
		"""Determine the alphabet for the given barcode format"""
		if not isinstance(alphabet, str):
			raise TypeError(f"Alphabets must be strings. Got {type(alphabet)}.")

		match fmt.lower():
			case "code39":
				chars = f"{string.digits}{string.ascii_uppercase} -.$/+%"
			case "gs1":
				chars = f"{string.digits}{string.ascii_uppercase}#-/"
			case "codabar" | "nw-7":
				chars = f"{string.digits}-$:/.+"
			case "code128" | "gs1_128":
				chars = f"{string.digits}{string.ascii_letters} {string.punctuation}"
			case "gtin" | "issn" | "itf" | "jan":
				chars = string.digits
			case f if f.startswith(("ean", "isbn", "pzn", "upc")):
				chars = string.digits

		if alphabet:
			if diff := set(alphabet) - set(chars):
				raise ValueError(f"Disallowed characters: {diff!r}")
			chars = alphabet

		# Sorted 0-9, A-Z, a-z, space, punctuation
		return ''.join(sorted(chars, key=lambda c: (not c.isalnum(), c)))

	# --------------------------------------------------------------------------
	@staticmethod
	def get_length(fmt, length=0) -> int:
		"""Determine the length for the given barcode format. A length
		may be provided for barcodes that don't have a standard length.
		"""
		std_length = {
			t: barcode.get_barcode_class(t).digits
			for t in barcode.PROVIDED_BARCODES
		}[fmt.lower()]

		if length == 0:
			return std_length or 8

		if not isinstance(length, int):
			raise TypeError("Barcode length must be an integer.")

		if length < 1:
			raise ValueError("Barcode length must be greater than 0.")

		if length > std_length > 0:
			raise ValueError(f"Barcode length can be at most {std_length}.")

		return length

	# --------------------------------------------------------------------------
	def _get_sectors(self):
		"""Create unique pairings that can be used to make managing impossibly
		large generative/search spaces possible on classical computers. These
		ranges are finite [0, self._limit) and their ordering can be randomized
		to create a more randomized sampling for creating codes or identifying
		spaces to search within for existing codes. To do this, we identify the
		magnitude of self._limit and then strategically iterate over each
		magnitude leading to self._limit and create relative and manageable range
		steps and extract them back out in "start", "stop" or "lo", "hi" pairs
		ex: [(0, 10000), (10000, 20000), ...]. The window for these pairings MUST
		slide relative to the magnitude lest we want a MemoryError due to generating
		a list too large to hold. It's also important to realize it MUST be a list
		if we want to take advantage of the random shuffling later. These "lo", "hi"
		pairings make generating random numbers within more realistic computational
		domains possible with some simple math.
		"""
		magnitude = len(str(self._limit)) - 1

		min_mag = min(4, magnitude)
		first_step = 10 ** min_mag

		ranges = [(0, first_step)]
		if self._limit < first_step:
			return ranges

		for m in range(magnitude):
			if m < min_mag:
				continue
			start = 10 ** m
			stop = 10 ** (m + 1)
			step = max(first_step, stop // first_step)
			chunks = range(start, stop + 1, step)
			ranges.extend(pairwise(chunks))

		return ranges

	# --------------------------------------------------------------------------
	def _to_code(self, x: int) -> str:
		"""Convert a decimal value to a barcode string"""
		if isinstance(x, str):
			return x

		s = ''
		while x:
			s += self.chars[x % self._base]
			x //= self._base
		return f"{''.join(s[::-1]):{self.chars[0]}>{self.length}}"

	# --------------------------------------------------------------------------
	def random_code(self, lo, hi) -> str:
		"""Create a random barcode string"""
		if lo > hi:
			raise ValueError("Lower bound must be less than upper bound.")

		ubound = min(hi, self._limit)
		return self._to_code(lo + secrets.randbelow(ubound - lo + 1))

	# --------------------------------------------------------------------------
	def generate(self, n=1) -> set[str]:
		"""Generate up to n barcodes. Less if the search space is exhausted."""
		if not isinstance(n, int):
			raise TypeError("n must be an integer.")
		if n < 1:
			raise ValueError("n must be greater than 0.")
		if not self._remaining:
			raise StopIteration("No more codes to generate.")

		secrets._sysrand.shuffle(self._sectors)

		n = min(n, self._remaining)
		print(f"{n=}")

		codes = set()
		while len(codes) < n:
			if not (self._sectors or codes):
				raise StopIteration("Stopping: Unlikely to generate code.")

			self._search(codes, n)

		self._used.update(codes)
		self._remaining -= len(codes)
		return codes

	# --------------------------------------------------------------------------
	def _search(self, codes, n):
		for sector in self._sectors.copy():
			if len(codes) == n:
				break

			found = False
			for _ in range(1000):
				if len(codes) == n:
					break

				code = self.random_code(*sector)
				if code not in self._used:
					found = True
					codes.add(code)

			if not found:
				self._sectors.remove(sector)


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

def to_code(S, N):
	base = len(S)
	def wrapped(x):
		if isinstance(x, str):
			return x

		s = ''
		while x:
			s += S[x % base]
			x //= base
		return f"{''.join(s[::-1]):{S[0]}>{N}}"
	return wrapped

def random_code(limit, converter):
	def wrapped(lo, hi):
		ubound = min(hi, limit)
		return converter(lo + secrets.randbelow(ubound - lo + 1))
	return wrapped

# ------------------------------------------------------------------------------
def main():
	# return
	fmt = "Code128"
	S = CodeGenerator.get_alphabet(fmt)
	N = CodeGenerator.get_length(fmt, 12)

	print("creating data")
	data = list(map(to_code(S, N), range(10**6)))
	G = CodeGenerator(fmt, length=N, used=data)

	for k, v in vars(G).items():
		match k:
			case "_used":
				print(k, len(v))
			case "_sectors":
				print(k, len(v))
			case _:
				print(k, repr(v))

	print("searching for code(s)")
	import time
	start = time.time()
	codes = G.generate(10**6)
	print(time.time() - start)

	print('-' * 100)
	if len(codes) > 20:
		print(f"codes={list(codes)[-100:]}")
	else:
		print(f"{codes=}")

	print('-' * 100)
	print(f"next={next(G)}")


if __name__ == "__main__":
	main()
