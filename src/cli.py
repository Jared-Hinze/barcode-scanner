# Python 3.6
# ------------------------------------------------------------------------------
# Processing
# ------------------------------------------------------------------------------
import keyboard
import msvcrt
from time import sleep

# ------------------------------------------------------------------------------
# Video Stream
# ------------------------------------------------------------------------------
import cv2
from pyzbar.pyzbar import decode, ZBarSymbol

# ------------------------------------------------------------------------------
# Custom
# ------------------------------------------------------------------------------
from database.sqlite import db

# ------------------------------------------------------------------------------
def scan(ip):
	winname = "Scanner"
	cv2.namedWindow(winname)
	cv2.setWindowProperty(winname, cv2.WND_PROP_TOPMOST, 1)
	cv2.moveWindow(winname, 1420, 0)

	video_feed = cv2.VideoCapture(f"rtsp://{ip}:8080/h264_pcm.sdp")
	if not video_feed.isOpened():
		print("cannot open camera")
		cv2.destroyAllWindows()
		return

	while True:
		ret, frame = video_feed.read()
		if not ret:
			print("can't recieve frame")
			return

		frame = cv2.resize(frame, (480, 207))

		barcodes = decode(frame, symbols=[ZBarSymbol.CODE128])
		for barcode in barcodes:
			highlight(frame, barcode)

		cv2.imshow(winname, frame)
		cv2.waitKey(1)

		if barcodes or keyboard.is_pressed("esc"):
			for rec in (db.lookup_code(code.data.decode("utf-8")) for code in barcodes):
				if not rec:
					print(f"Could not find code")
					continue
				code = rec["code"]
				if rec["used"]:
					print(f"WARNING: {code} already used")
					continue
				db.update(code)
				print(f"ACCEPTED: {code}")
			cv2.destroyAllWindows()
			return

# ------------------------------------------------------------------------------
def highlight(frame, barcode):
	x, y, w, h = barcode.rect

	cv2.rectangle(
		frame,
		(x-10, y-10),
		(x + w+10, y + h+10),
		(255, 0, 0),
		2
	)
	if barcode.data:
		print(f'{barcode.type} - {barcode.data.decode("utf-8")}')

# ------------------------------------------------------------------------------
def mode_select():
	print('\n'.join([
		"[enter]: Scanning Mode",
		"[space]: Manual Mode",
		"  [esc]: Quit\n",
	]))
	while True:
		key = keyboard.read_key()
		# Flush the input buffer
		while msvcrt.kbhit():
			msvcrt.getch()

		if key == "enter":
			print('\n'.join([
				"Scanning mode",
				"  Scan a barcode or press Esc to exit\n"
			]))
			scan(ip)
			break
		elif key == "space":
			print("Manual mode")
			db.check_code(input("Enter Code: ").strip())
			break
		elif key == 'esc':
			terminate()

	print('')

# ------------------------------------------------------------------------------
def run(ip):
	while True:
		mode_select()
		# Keep this to make sure we don't think a keypress from
		# scan is still being held down out here
		sleep(1)

# ------------------------------------------------------------------------------
def terminate():
	try:
		cv2.destroyAllWindows()
	except Exception:
		pass
	finally:
		exit()

# ------------------------------------------------------------------------------
if __name__ == "__main__":
	print('')
	ip = input("Enter IP: ").strip()
	print('')

	# Keep this to make sure we don't think a keypress from
	# input is still being held down out here
	sleep(1)

	run(ip)
