# Python 3.6
# ------------------------------------------------------------------------------------
# Tkinter & Windows Support
# ------------------------------------------------------------------------------------
import tkinter as tk
from tkinter import EventType
from tkinter import font, ttk
from ctypes import windll

# ------------------------------------------------------------------------------------
# Video Stream
# ------------------------------------------------------------------------------------
import cv2
import queue
from PIL import Image, ImageTk, ImageGrab
from pyzbar.pyzbar import decode, ZBarSymbol
from threading import Thread

# ------------------------------------------------------------------------------------
# Processing
# ------------------------------------------------------------------------------------
import keyboard
import math
import regex
import string
import sys
import traceback
from collections import namedtuple
from datetime import datetime
from simpleaudio import WaveObject

# ------------------------------------------------------------------------------------
# Custom
# ------------------------------------------------------------------------------------
import db
from paths import DIR_BASE, DIR_IMAGES, DIR_SOUNDS

# ------------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------------
DEBUG = True

Font = namedtuple("Font", ["family", "size", "weight"])
Font.__new__.__defaults__ = (font.NORMAL, )

# ------------------------------------------------------------------------------------
# Helper Function
# ------------------------------------------------------------------------------------
def log(msg):
	msg = regex.sub(r"\s+", ' ', msg)
	line = f"[{datetime.now().isoformat()}] {msg}"
	with open(DIR_BASE.joinpath("log.txt"), mode='a') as f:
		f.write(line + '\n')
	print(line)

# ------------------------------------------------------------------------------------
# Psuedo Enums
# ------------------------------------------------------------------------------------
class Sounds:
	INVALID = WaveObject.from_wave_file(str(DIR_SOUNDS.joinpath("invalid.wav")))
	ERROR = WaveObject.from_wave_file(str(DIR_SOUNDS.joinpath("error.wav")))
	WARN = WaveObject.from_wave_file(str(DIR_SOUNDS.joinpath("warn.wav")))
	ACCEPT = WaveObject.from_wave_file(str(DIR_SOUNDS.joinpath("accept.wav")))
	CONNECTION_FAILED = WaveObject.from_wave_file(str(DIR_SOUNDS.joinpath("connection_failed.wav")))

# ====================================================================================
class SystemColors:
	CARET = "#E3E3DC"

# ====================================================================================
class BackgroundColors:
	MAIN = "#282923"
	TITLE_BAR = "#181915"
	TITLE_BTN_ACTIVE = "#22231F"
	CLOSE_BTN_ACTIVE = "#E81123"
	ENTRY_HIGHLIGHT = "#47473D"
	INPUT_DISABLED = "#181915"
	SCAN_BTN = "#2E2F2B"
	SCAN_BTN_ACTIVE = SCAN_BTN_DISABLED = "#464646"
	SCAN_OVERLAY = "#000000"

# ====================================================================================
class ScanDisplayColors:
	INVALID = "#AC6A91"
	ERROR = "#E32639"
	WARNING = "#FD9622"
	ACCEPTED = "#A6CE28"
	WAITING = "#E7DB6A"
	CONNECTING = "#67C5A7"

# ====================================================================================
class TextColors:
	TITLE = TITLE_CLOSE = "#838381"
	TITLE_BTN = "#FFFFFF"
	CLOSE_BTN_ACTIVE = "#FEECED"
	ENTRY_HEADER = "#74705D"
	ENTRY = "#F8F8F2"
	ENTRY_HIGHLIGHT = "#F8F8C7"
	SCAN_BTN = "#FF9800"
	SCAN_BTN_ACTIVE = SCAN_BTN_DISABLED = "#FF9800"

# ------------------------------------------------------------------------------------
# Custom Widgets
# ------------------------------------------------------------------------------------
class FrmButton(ttk.Frame):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, frame_kwargs, button_kwargs):
		super().__init__(parent, **frame_kwargs)
		self.pack_propagate(0)

		self.btn = ttk.Button(self, **button_kwargs)
		self.btn.pack(fill=tk.BOTH, expand=True)

# ====================================================================================
class FrmCanvas(ttk.Frame):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, frame_kwargs, canvas_kwargs):
		super().__init__(parent, **frame_kwargs)
		self.pack_propagate(0)

		self.canvas = tk.Canvas(self, **canvas_kwargs)
		self.canvas.pack(fill=tk.BOTH, expand=True)

# ====================================================================================
class StdEntry(ttk.Entry):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, rgx=None, max_chars=None, transform=lambda s: s, **kwargs):
		self.textvariable = kwargs.pop("textvariable", tk.StringVar())

		self.data = tk.StringVar()
		self.data.trace_add("write", lambda *args: self.data.set(transform(self.data.get())))

		super().__init__(parent,
			textvariable=self.data,
			font=Font(family="Courier New", size=20, weight=font.BOLD),
			style="StdEntry.TEntry",
			**kwargs
		)
		vcmd = (self.register(self.on_validate), "%P")
		self.configure(validate=tk.ALL, validatecommand=vcmd)

		self.rgx = rgx if rgx is not None else regex.compile(r".*")
		self.max_chars = max_chars if max_chars is not None else math.inf

	# --------------------------------------------------------------------------------
	def on_validate(self, new_value):
		if len(new_value) <= self.max_chars and self.rgx.match(new_value):
			return True
		else:
			self.bell()
			return False

	# --------------------------------------------------------------------------------
	def is_valid(self):
		value = self.get()
		return len(value) == self.max_chars and self.rgx.match(value)

# ====================================================================================
class StdLabelFrame(ttk.LabelFrame):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, text, **kwargs):
		self.lbl = ttk.Label(parent, text=text, style="StdEntry.TLabel")
		super().__init__(parent, labelwidget=self.lbl, **kwargs)

# ====================================================================================
class FrmEntry(StdLabelFrame):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, frame_kwargs, entry_kwargs):
		super().__init__(parent, **frame_kwargs)
		self.pack_propagate(0)

		self.entry = StdEntry(self, **entry_kwargs)
		self.entry.pack(fill=tk.BOTH, expand=True)
		self.entry.bind("<FocusOut>",
			lambda e: self.entry.textvariable.set(self.entry.get())
		)

# ====================================================================================
class ScanEntry(StdEntry):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, **kwargs):
		super().__init__(parent,
			rgx=regex.compile(r"^\L<symbols>*$", symbols=string.ascii_letters + string.digits),
			max_chars=12,
			transform=lambda s: s.upper(),
			**kwargs
		)

# ====================================================================================
class FrmScanEntry(StdLabelFrame):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, frame_kwargs, entry_kwargs):
		super().__init__(parent, **frame_kwargs)
		self.pack_propagate(0)

		self.entry = ScanEntry(self, **entry_kwargs)
		self.entry.pack(fill=tk.BOTH, expand=True)

# ====================================================================================
class FrmLabel(ttk.Frame):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, frame_kwargs, label_kwargs):
		super().__init__(parent, **frame_kwargs)
		self.pack_propagate(0)

		# Simulate transparency
		style = frame_kwargs.get("style") or "TFrame"
		background = ttk.Style().lookup(style, "background")

		self.default_text = label_kwargs.pop("default_text", '') or label_kwargs.get("text") or ''
		self.textvariable = label_kwargs.get("textvariable")
		self.lbl = ttk.Label(self,
			background=background,
			wraplength=frame_kwargs["width"],
			**label_kwargs
		)
		self.lbl.pack(anchor=tk.CENTER, expand=True)
		self.lbl.update()

		self.resetting = None

	# --------------------------------------------------------------------------------
	def reset(self, timeout=3000):
		if self.resetting:
			self.lbl.after_cancel(self.resetting)

		# ----------------------------------------------------------------------------
		def _reset():
			self.lbl.configure(foreground=ScanDisplayColors.WAITING)
			if self.textvariable is not None:
				self.textvariable.set(self.default_text)
			else:
				self.lbl.configure(text=self.default_text)

		# ----------------------------------------------------------------------------
		self.resetting = self.lbl.after(timeout, _reset)

		return self.resetting

# ------------------------------------------------------------------------------------
# Layouts
# ------------------------------------------------------------------------------------
class TitleBar(ttk.Frame):
	# --------------------------------------------------------------------------------
	def __init__(self, parent):
		self.window = parent.master
		self.set_styles(self.window.style)

		super().__init__(parent,
			width=self.window.winfo_width(), height=40,
			style="title_bar.TFrame",
		)
		self.grid(column=0, row=0, columnspan=10)
		self.pack_propagate(0)

		self.icon = tk.PhotoImage(file=DIR_IMAGES.joinpath("icon.png")).subsample(20)
		self.frm_title = FrmLabel(self,
			frame_kwargs={
				"width": 250, "height": 40,
				"style": "title_bar.TFrame",
			},
			label_kwargs={
				"text": " Barcode Scanner (SkateAway)",
				"image": self.icon,
				"compound": tk.LEFT,
				"style": "title_text.TLabel",
			}
		)
		self.frm_title.pack(side=tk.LEFT)

		self.bind_move(self)
		self.bind_move(self.frm_title.lbl)

		self.frm_minimize_button = FrmButton(self,
			frame_kwargs={"width": 50, "height": 40},
			button_kwargs={
				"text": "__",
				"command": lambda: self.window.hide_window(None),
				"style": "title_btns.TButton",
			},
		)
		self.frm_minimize_button.pack(side=tk.RIGHT)
		self.frm_minimize_button.update()

		self.frm_close_button = FrmButton(self,
			frame_kwargs={"width": 50, "height": 40},
			button_kwargs={
				"text": 'X',
				"command": self.window.root.destroy,
				"style": "title_close.TButton",
			},
		)
		self.frm_close_button.pack(side=tk.RIGHT, before=self.frm_minimize_button)
		self.frm_close_button.update()

	# --------------------------------------------------------------------------------
	def set_styles(self, style):
		style.configure("title_bar.TFrame",
			background=BackgroundColors.TITLE_BAR,
		)
		style.configure("title_text.TLabel",
			foreground=TextColors.TITLE,
			font=Font(family="Gabriola", size=14, weight=font.BOLD),
		)
		style.configure("title_btns.TButton",
			background=BackgroundColors.TITLE_BAR,
			foreground=TextColors.TITLE_BTN,
			borderwidth=0,
			font=Font(family="System", size=12)
		)
		style.map("title_btns.TButton",
			background=[("active", BackgroundColors.TITLE_BTN_ACTIVE)],
		)
		style.configure("title_close.TButton",
			background=BackgroundColors.TITLE_BAR,
			foreground=TextColors.TITLE_CLOSE,
			borderwidth=0,
			font=Font(family="System", size=12)
		)
		style.map("title_close.TButton",
			background=[("active", BackgroundColors.CLOSE_BTN_ACTIVE)],
			foreground=[("active", TextColors.CLOSE_BTN_ACTIVE)]
		)

	# --------------------------------------------------------------------------------
	def bind_move(self, widget):
		widget.bind("<Button-1>", self.start_move)
		widget.bind("<B1-Motion>", self.moving)
		widget.bind("<ButtonRelease-1>", self.stop_move)

	# --------------------------------------------------------------------------------
	def start_move(self, event):
		self.x, self.y = event.x, event.y

	# --------------------------------------------------------------------------------
	def stop_move(self, event):
		self.x = self.y = None

	# --------------------------------------------------------------------------------
	def moving(self, event):
		self.window.geometry(f"+{event.x_root - self.x}+{event.y_root - self.y}")

# ====================================================================================
class LeftPane(ttk.Frame):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, shared_variables):
		self.window = parent.master

		super().__init__(parent)
		self.grid(column=0, row=1, columnspan=5, rowspan=10)
		self.pack_propagate(0)

		result = shared_variables["results"]
		self.frm_results = FrmResults(self,
			label_kwargs={
				"default_text": result.get(),
				"textvariable": result,
				"justify": tk.CENTER,
			},
		)
		self.frm_results.update()

		self.frm_connection = FrmConnection(self,
			label_kwargs={},
			entry_kwargs={"textvariable": shared_variables["connection_str"]},
		)
		self.frm_connection.update()

# ====================================================================================
class FrmResults(ttk.Frame):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, label_kwargs):
		self.window = parent.window

		super().__init__(parent)
		self.grid(column=0, row=1, columnspan=5, rowspan=9)
		self.update()
		self.pack_propagate(0)

		self.frm_label = FrmLabel(self,
			frame_kwargs={
				"width": 490, "height": 586,
				"borderwidth": 5,
				"relief": tk.SUNKEN,
				"style": "TFrame",
			},
			label_kwargs=label_kwargs,
		)
		self.frm_label.grid(column=0, row=1, columnspan=5, rowspan=9)
		self.frm_label.update()

		self.debugging = None

	# --------------------------------------------------------------------------------
	def handle_data(self, code, valid=True, debug_rec=None):
		rec = debug_rec if debug_rec else db.lookup_code(code)

		if not (rec and valid):
			valid = False
			Sounds.INVALID.play()
			msg = "Invalid Barcode"
			if code:
				msg += f"\n\n{code}"
			self.frm_label.lbl.configure(foreground=ScanDisplayColors.INVALID)
		elif rec.get("error"):
			valid = False
			Sounds.ERROR.play()
			msg = f"ERROR:\n\nSee logs for details."
			self.frm_label.lbl.configure(foreground=ScanDisplayColors.ERROR)
		elif rec.get("used"):
			Sounds.WARN.play()
			msg = f"WARNING:\n\n{code}\n\nPreviously Used"
			self.frm_label.lbl.configure(foreground=ScanDisplayColors.WARNING)
		else:
			Sounds.ACCEPT.play()
			msg = f"Accepted:\n\n{code}"
			self.frm_label.lbl.configure(foreground=ScanDisplayColors.ACCEPTED)
			db.update(code)

		log(msg)
		if rec.get("error"):
			log(f'ERROR: {rec["error"]}')

		return (msg, valid)

	# --------------------------------------------------------------------------------
	def show_result(self, event, sender=None):
		if event.type == EventType.KeyPress:
			entry_valid = sender.is_valid()
			msg, actually_valid = self.handle_data(sender.get(), entry_valid)

			if actually_valid:
				sender.delete(0, "end")

		elif event.type == EventType.VirtualEvent:
			code = data = sender.data

			if isinstance(data, dict):
				code = data.get("code") or ''
				msg, _ = self.handle_data(code, debug_rec=data)
			else:
				msg, _ = self.handle_data(code)

			scan_entry = self.window.right_pane.frm_input.frm_scan_entry.entry
			scan_entry.configure(state=tk.NORMAL)
			scan_entry.delete(0, "end")
			scan_entry.insert(0, code)
			scan_entry.configure(state=tk.DISABLED)

		sender.textvariable.set(msg)

		self.frm_label.reset()

	# --------------------------------------------------------------------------------
	def debug_display(self, event):
		self.event_generate("<<Scanning>>")

		sender = self.window.right_pane.frm_scan_view

		key = event.keysym
		if key == "exclam":
			sender.data = {"error": "This is a fake error message"}
		elif key == "at":
			sender.data = {} # Invalid Barcode ie lookup failed
		elif key == "numbersign":
			sender.data = {"code": "TEST1234", "used": True}
		elif key == "dollar":
			sender.data = {"code": "TEST9876", "used": False}
		else:
			raise ValueError("debug_display - something went wrong")

		event.type = EventType.VirtualEvent
		self.show_result(event, sender)
		sender.data = None

		if self.debugging:
			self.after_cancel(self.debugging)
		self.debugging = self.after(3000, lambda: self.event_generate("<<!Scanning>>"))

# ====================================================================================
class FrmConnection(ttk.Frame):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, label_kwargs, entry_kwargs):
		self.window = parent.window

		super().__init__(parent,
			borderwidth=5,
			relief=tk.SUNKEN,
		)
		self.grid(column=0, row=10, columnspan=5)
		self.pack_propagate(0)

		self.frm_label = FrmLabel(self,
			frame_kwargs={"width": 40, "height": 40},
			label_kwargs={},
		)
		# Must use geo manager + update() to have valid winfo
		self.frm_label.grid(column=0, row=10, padx=5)
		self.frm_label.update()

		self._image = Image.open(DIR_IMAGES.joinpath("browser.png"))
		self.image = ImageTk.PhotoImage(
			self._image.resize(
				(self.frm_label.winfo_width(), self.frm_label.winfo_height()),
				Image.ANTIALIAS
			)
		)
		self.frm_label.lbl.configure(image=self.image)

		self.frm_entry = FrmEntry(self,
			frame_kwargs={
				"width": 420, "height": 60,
				"text": "IP:Port",
			},
			entry_kwargs=entry_kwargs,
		)
		self.frm_entry.grid(column=2, row=10, columnspan=3, padx=5, pady=(0, 5))
		self.frm_entry.update()

	# --------------------------------------------------------------------------------
	def disable(self, event):
		self.configure(style="disabled.TFrame")
		self.frm_label.lbl.configure(background=ttk.Style().lookup("disabled.TFrame", "background"))
		self.frm_entry.configure(style="disabled.TLabelframe")
		self.frm_entry.lbl.configure(style="disabled.StdEntry.TLabel")
		self.frm_entry.entry.configure(state=tk.DISABLED)

	# --------------------------------------------------------------------------------
	def enable(self, event):
		self.configure(style="TFrame")
		self.frm_label.lbl.configure(background=ttk.Style().lookup("TFrame", "background"))
		self.frm_entry.configure(style="TLabelframe")
		self.frm_entry.lbl.configure(style="StdEntry.TLabel")
		self.frm_entry.entry.configure(state=tk.NORMAL)

# ====================================================================================
class RightPane(ttk.Frame):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, shared_variables):
		self.window = parent.master

		super().__init__(parent)
		self.grid(column=5, row=1, columnspan=5, rowspan=10)
		self.update()
		self.pack_propagate(0)

		self.frm_scan_view = FrmScanView(self, shared_variables)

		self.frm_input = FrmInput(self,
			button_kwargs={
				"text": "Scan",
				"command": self.frm_scan_view.scan_barcode,
				"style": "input.TButton",
			},
			entry_kwargs={"textvariable": shared_variables["results"]},
		)
		entry = self.frm_input.frm_scan_entry.entry
		entry.bind("<Return>", lambda e: self.window.left_pane.frm_results.show_result(e, sender=entry))

# ====================================================================================
class VideoStream:
	# --------------------------------------------------------------------------------
	def __init__(self, connection_str, timeout):
		self.connection_str = connection_str
		self.timeout = timeout // 1000 # ms -> seconds
		self.stream = cv2.VideoCapture()
		self.status = self.frame = None
		self.scanning = False

	# --------------------------------------------------------------------------------
	def __del__(self):
		self.disconnect()

	# --------------------------------------------------------------------------------
	def connect(self):
		_queue = queue.Queue()
		connection_str = f"rtsp://{self.connection_str.get()}/h264_pcm.sdp"
		log(f"Contacting {connection_str}")

		# ----------------------------------------------------------------------------
		def get_video_connection(connection_str):
			_queue.put(cv2.VideoCapture(connection_str))

		# ----------------------------------------------------------------------------
		thread = Thread(target=get_video_connection, args=(connection_str,))
		thread.daemon = True
		thread.start()

		try:
			self.stream = _queue.get(block=True, timeout=self.timeout)
			log("Connected")
		except queue.Empty:
			self.disconnect()
			raise

	# --------------------------------------------------------------------------------
	def disconnect(self):
		if self.scanning:
			self.scanning = False
		if self.stream.isOpened():
			self.stream = cv2.VideoCapture()

	# --------------------------------------------------------------------------------
	def start(self):
		self.scanning = True
		thread = Thread(target=self.read, args=())
		thread.daemon = True
		thread.start()

	# --------------------------------------------------------------------------------
	def read(self):
		while self.scanning:
			try:
				if self.stream.isOpened():
					(self.status, self.frame) = self.stream.read()
			except cv2.error:
				self.disconnect()

	# --------------------------------------------------------------------------------
	def stop(self):
		self.scanning = False

	# --------------------------------------------------------------------------------
	def get_frame(self):
		return (self.status, self.frame)

# ====================================================================================
class FrmScanView(ttk.Frame):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, shared_variables):
		self.window = parent.window

		self.textvariable = shared_variables["results"]

		super().__init__(parent)
		self.update()
		self.pack_propagate(0)

		frame_kwargs = {
			"width": 1034, "height": 586,
			"borderwidth": 5,
			"relief": tk.SUNKEN,
			"style": "TFrame",
		}
		self.frm_canvas = FrmCanvas(parent,
			frame_kwargs=frame_kwargs,
			canvas_kwargs={"highlightthickness": 0}
		)
		self.frm_canvas.grid(column=5, row=1, columnspan=5, rowspan=9)
		self.frm_canvas.update()

		self.frm_label = FrmLabel(parent,
			frame_kwargs=frame_kwargs,
			label_kwargs={"text": "Waiting for source..."},
		)
		self.frm_label.grid(column=5, row=1, columnspan=5, rowspan=9)
		self.frm_label.update()

		self.connection_timeout = 5000 # ms
		self.stream = VideoStream(shared_variables["connection_str"], self.connection_timeout)
		self.data = None

		self.connecting = None

		size = (self.frm_canvas.winfo_width(), 35)
		alpha = int(0.5 * 255) # opacity
		rgba = self.frm_canvas.winfo_rgb(BackgroundColors.SCAN_OVERLAY) + (alpha,)
		self.overlay = Image.new("RGBA", size, rgba)
		self._overlay = ImageTk.PhotoImage(self.overlay)

		self.scan_background = self.frm_canvas.canvas.create_image(
			self.frm_canvas.winfo_width() / 2, self.frm_canvas.winfo_height() - 10,
			image=self._overlay,
			anchor=tk.S,
		)
		self.scan_text = self.frm_canvas.canvas.create_text(
			self.frm_canvas.winfo_width() / 2, self.frm_canvas.winfo_height() - 15,
			text="Press Esc to Cancel",
			font=Font(family="Terminal", size=20),
			fill=ScanDisplayColors.WAITING,
			anchor=tk.S,
			justify=tk.CENTER,
		)

	# --------------------------------------------------------------------------------
	def scan_barcode(self):
		try:
			self.event_generate("<<Scanning>>")

			if self.connecting:
				self.after_cancel(self.connecting)

			msg = "Trying to connect..."
			log(msg)
			self.frm_label.lbl.configure(
				text=msg,
				foreground=ScanDisplayColors.CONNECTING,
			)
			self.frm_label.lbl.update()

			self.pre_scan()
			self.scan()
		except queue.Empty:
			Sounds.CONNECTION_FAILED.play()

			msg = "Can't find source"
			log(msg)
			self.frm_label.lbl.configure(
				text=msg,
				foreground=ScanDisplayColors.ERROR,
			)
			self.frm_label.lbl.update()

			self.post_scan()
		except Exception as e:
			self.is_valid = False
			self.data["error"] = str(e)
			self.event_generate("<<ScanComplete>>")
			self.post_scan()
		finally:
			self.connecting = self.frm_label.reset()

	# --------------------------------------------------------------------------------
	def pre_scan(self):
		self.stream.connect()
		self.stream.start()
		self.frm_canvas.tkraise()

	# --------------------------------------------------------------------------------
	def scan(self):
		if keyboard.is_pressed("esc"):
			self.post_scan()

		ret, frame = self.stream.get_frame()
		if ret:
			size = (
				self.frm_canvas.winfo_width() - 10,
				self.frm_canvas.winfo_height() - 10
			)
			frame = cv2.resize(frame, size)

			barcode = next(iter(decode(frame, symbols=[ZBarSymbol.CODE128])), None)
			if barcode:
				x, y, w, h = barcode.rect

				cv2.rectangle(frame,
					(x - 10, y - 10), (x + w + 10, y + h + 10),
					(255, 0, 0), 2
				)
				if barcode.data:
					self.data = barcode.data.decode("utf-8")
					log(f"{barcode.type} - {self.data}")

			self.frame = image = ImageTk.PhotoImage(
				image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)),
			)
			self.frm_canvas.canvas.create_image(0, 0, image=self.frame, anchor=tk.NW)
			self.frm_canvas.canvas.tag_raise(self.scan_background)
			self.frm_canvas.canvas.tag_raise(self.scan_text)

		if self.data:
			self.event_generate("<<ScanComplete>>")
			self.after(3000, self.post_scan)
		elif self.stream.scanning:
			self.frm_canvas.canvas.after(1, self.scan)

	# --------------------------------------------------------------------------------
	def post_scan(self):
		self.frm_label.tkraise()
		self.stream.stop()
		self.stream.disconnect()
		self.data = None
		self.event_generate("<<!Scanning>>")

# ====================================================================================
class FrmInput(ttk.Frame):
	# --------------------------------------------------------------------------------
	def __init__(self, parent, button_kwargs, entry_kwargs):
		self.window = parent.window
		self.set_styles(self.window.style)

		super().__init__(parent,
			borderwidth=5,
			relief=tk.SUNKEN,
		)
		self.grid(column=5, row=10, columnspan=5)
		self.pack_propagate(0)

		self.frm_btn = FrmButton(self,
			frame_kwargs={"width": 135, "height": 55},
			button_kwargs=button_kwargs,
		)
		self.frm_btn.grid(column=5, row=10, padx=(5, 0), pady=(5, 0))
		self.frm_btn.update()

		self.frm_scan_entry = FrmScanEntry(self,
			frame_kwargs={
				"width": 874, "height": 60,
				"text": "Enter Code",
			},
			entry_kwargs=entry_kwargs,
		)
		self.frm_scan_entry.grid(column=6, row=10, columnspan=4, padx=5, pady=(0, 5))
		self.frm_scan_entry.update()

	# --------------------------------------------------------------------------------
	def disable(self, event):
		self.configure(style="disabled.TFrame")
		self.frm_btn.btn.configure(state=tk.DISABLED)

		self.frm_scan_entry.configure(style="disabled.TLabelframe")
		self.frm_scan_entry.lbl.configure(style="disabled.StdEntry.TLabel")
		self.frm_scan_entry.entry.delete(0, "end")
		self.frm_scan_entry.entry.configure(state=tk.DISABLED)

	# --------------------------------------------------------------------------------
	def enable(self, event):
		self.configure(style="TFrame")
		self.frm_btn.btn.configure(state=tk.NORMAL)

		self.frm_scan_entry.configure(style="TLabelframe")
		self.frm_scan_entry.lbl.configure(style="StdEntry.TLabel")
		self.frm_scan_entry.entry.configure(state=tk.NORMAL)
		self.frm_scan_entry.entry.delete(0, "end")

	# --------------------------------------------------------------------------------
	def set_styles(self, style):
		style.configure("input.TButton",
			background=BackgroundColors.SCAN_BTN,
			foreground=TextColors.SCAN_BTN,
			borderwidth=5,
			font=Font(family="Segoe UI Black", size=14)
		)
		style.map("input.TButton",
			background=[
				("active", BackgroundColors.SCAN_BTN_ACTIVE),
				("disabled", BackgroundColors.SCAN_BTN_DISABLED)
			],
			foreground=[
				("active", TextColors.SCAN_BTN_ACTIVE),
				("disabled", TextColors.SCAN_BTN_DISABLED),
			],
		)

# ------------------------------------------------------------------------------------
# Application
# ------------------------------------------------------------------------------------
class Root(tk.Tk):
	# --------------------------------------------------------------------------------
	def __init__(self):
		super().__init__()
		self.attributes("-alpha", 0.0)
		# Using this to be able to create an image for taskbar preview
		self.ctrl_window = tk.Canvas(self)
		self.ctrl_window.pack(fill=tk.BOTH, expand=True)

# ====================================================================================
class BarcodeScanner(tk.Toplevel):
	# --------------------------------------------------------------------------------
	def __init__(self, root):
		self.root = root
		self.icon = tk.PhotoImage(file=DIR_IMAGES.joinpath("icon.png"))

		super().__init__(root)

		self.geometry("1524x701+385+152")
		self.overrideredirect(True)

		self.set_styles()
		self.set_widgets()

		self.root.title("Barcode Scanner (SkateAway)")
		self.root.iconphoto(False, self.icon)
		self.root.ctrl_window.bind("<Map>", self.show_window)
		self.root.ctrl_window.bind("<Unmap>", self.hide_window)

		if DEBUG:
			proxy = self.left_pane.frm_results
			self.bind("<Control-Shift-!>", lambda e: proxy.debug_display(e))
			self.bind("<Control-Shift-@>", lambda e: proxy.debug_display(e))
			self.bind("<Control-Shift-#>", lambda e: proxy.debug_display(e))
			self.bind("<Control-Shift-$>", lambda e: proxy.debug_display(e))

		self.bind("<<Scanning>>", self.left_pane.frm_connection.disable)
		self.bind("<<Scanning>>", self.right_pane.frm_input.disable, add='+')

		self.bind("<<!Scanning>>", self.left_pane.frm_connection.enable)
		self.bind("<<!Scanning>>", self.right_pane.frm_input.enable, add='+')

		self.bind("<<ScanComplete>>", lambda e: self.left_pane.frm_results.show_result(e, sender=self.right_pane.frm_scan_view))

		# Present the screen on top
		self.lift()
		# Take a snapshot of it for the taskbar preview
		self.snapshot()

	# --------------------------------------------------------------------------------
	def show_window(self, event):
		self.deiconify()
		self.after(500, self.snapshot)

	# --------------------------------------------------------------------------------
	def hide_window(self, event):
		self.snapshot()
		self.withdraw()

	# --------------------------------------------------------------------------------
	def snapshot(self):
		w, h = self.winfo_width(), self.winfo_height()
		x, y = self.winfo_x(), self.winfo_y()

		self.screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
		self._screenshot = ImageTk.PhotoImage(image=self.screenshot)
		self.root.ctrl_window.configure(width=w, height=h)
		self.root.ctrl_window.create_image(w / 2, h / 2, image=self._screenshot)

	# --------------------------------------------------------------------------------
	def set_styles(self):
		self.style = ttk.Style()
		self.style.theme_use("alt")

		self.style.configure("TFrame",
			background=BackgroundColors.MAIN,
		)
		self.style.configure("TLabel",
			foreground=ScanDisplayColors.WAITING,
			font=Font(family="Terminal", size=20, weight=font.BOLD),
		)
		self.style.configure("TLabelframe",
			background=BackgroundColors.MAIN,
			borderwidth=1,
		)

		self.style.configure("StdEntry.TLabel",
			background=BackgroundColors.MAIN,
			foreground=TextColors.ENTRY_HEADER,
			font=Font(family="Terminal", size=8),
		)
		self.style.configure("StdEntry.TEntry",
			background=BackgroundColors.MAIN,
			insertcolor=SystemColors.CARET,
			foreground=TextColors.ENTRY,
			fieldbackground=BackgroundColors.MAIN,
			selectbackground=BackgroundColors.ENTRY_HIGHLIGHT,
			selectforeground=TextColors.ENTRY_HIGHLIGHT,
			relief=tk.FLAT,
		)
		self.style.layout("StdEntry.TEntry", [
			("Entry.highlight", {
				"sticky": "nswe",
				"children":	[("Entry.border", {
					"border": "1",
					"sticky": "nswe",
					"children": [("Entry.padding", {
						"sticky": "nswe",
						"children": [("Entry.textarea", {
							"sticky": "nswe"})]
					})]
				})]
			})]
		)
		self.style.map("StdEntry.TEntry",
			background=[("disabled", BackgroundColors.INPUT_DISABLED)],
		)

		self.style.configure("disabled.TFrame",
			background=BackgroundColors.INPUT_DISABLED,
		)
		self.style.configure("disabled.TLabelframe",
			background=BackgroundColors.INPUT_DISABLED,
			borderwidth=1,
		)
		self.style.configure("disabled.StdEntry.TLabel",
			background=BackgroundColors.INPUT_DISABLED,
			foreground=TextColors.ENTRY_HEADER,
			font=Font(family="Terminal", size=8),
		)

	# --------------------------------------------------------------------------------
	def set_widgets(self):
		self.frm_root = ttk.Frame(self)
		self.frm_root.grid(column=0, row=0, columnspan=10, rowspan=10)
		self.frm_root.update()

		connection_str = tk.StringVar()
		result = tk.StringVar()
		result.set("Waiting for input...")

		shared_variables = {
			"results": result,
			"connection_str": connection_str,
		}
		self.title_bar = TitleBar(self.frm_root)
		self.left_pane = LeftPane(self.frm_root, shared_variables)
		self.right_pane = RightPane(self.frm_root, shared_variables)

# ====================================================================================
if __name__ == "__main__":
	try:
		print("hi")
		raise
		BarcodeScanner(Root()).mainloop()
	except Exception:
		log(traceback.format_exc())