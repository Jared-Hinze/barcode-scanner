# Built-in Libraries
# N/A

# Third Party Libraries
from pytest import CaptureFixture, LogCaptureFixture

# Local Libraries
# N/A


# ==============================================================================
def has_message(capturer, msg, predicate=str.__contains__):
	if isinstance(capturer, LogCaptureFixture):
		return any(predicate(m, msg) for m in capturer.messages)
	elif isinstance(capturer, CaptureFixture):
		out, err = capturer.readouterr()
		return predicate(out, msg) or predicate(err, msg)

	raise Exception("Unknown capture method.")
