import tkinter as tk
from tkinter import messagebox
import serial
import time

PORT = "/dev/rfcomm0"
BAUD = 9600

CMD = {
    "F": b"F",
    "B": b"B",
    "L": b"L",
    "R": b"R",
    "G": b"G",
    "I": b"I",
    "H": b"H",
    "J": b"J",
    "S": b"S",
}

KEY_MAP = {
    "w": "F",
    "W": "F",
    "Up": "F",
    "s": "B",
    "S": "B",
    "Down": "B",
    "a": "L",
    "A": "L",
    "Left": "L",
    "d": "R",
    "D": "R",
    "Right": "R",
}


class RobotController(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("LLANERO Bluetooth Control")
        self.geometry("420x500")
        self.resizable(False, False)
        self.configure(bg="#101820")

        self.serial_conn = None
        self.connected = False
        self.pressed_keys = set()
        self.active_mouse = set()

        self.build_ui()
        self.bind_keys()

    def build_ui(self):
        title = tk.Label(
            self,
            text="LLANERO CONTROL",
            font=("Arial", 18, "bold"),
            fg="cyan",
            bg="#101820"
        )
        title.pack(pady=10)

        self.status_label = tk.Label(
            self,
            text="DISCONNECTED",
            font=("Arial", 12, "bold"),
            fg="red",
            bg="#101820"
        )
        self.status_label.pack(pady=5)

        port_label = tk.Label(
            self,
            text="Port: " + PORT,
            font=("Arial", 11),
            fg="white",
            bg="#101820"
        )
        port_label.pack(pady=5)

        btn_frame = tk.Frame(self, bg="#101820")
        btn_frame.pack(pady=10)

        self.connect_btn = tk.Button(
            btn_frame,
            text="CONNECT",
            font=("Arial", 11, "bold"),
            width=12,
            bg="green",
            fg="white",
            command=self.toggle_connection
        )
        self.connect_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = tk.Button(
            btn_frame,
            text="STOP",
            font=("Arial", 11, "bold"),
            width=12,
            bg="red",
            fg="white",
            command=lambda: self.send_command("S")
        )
        self.stop_btn.grid(row=0, column=1, padx=5)

        self.last_cmd_label = tk.Label(
            self,
            text="Last command: None",
            font=("Arial", 12),
            fg="white",
            bg="#101820"
        )
        self.last_cmd_label.pack(pady=10)

        pad = tk.Frame(self, bg="#101820")
        pad.pack(pady=20)

        self.buttons = {}

        layout = [
            [("G", "G"), ("F", "F"), ("I", "I")],
            [("L", "L"), ("S", "S"), ("R", "R")],
            [("H", "H"), ("B", "B"), ("J", "J")],
        ]

        for r, row in enumerate(layout):
            for c, item in enumerate(row):
                cmd, label = item
                btn = tk.Label(
                    pad,
                    text=label,
                    font=("Arial", 20, "bold"),
                    width=4,
                    height=2,
                    bg="#2a2a2a",
                    fg="white",
                    relief="raised",
                    bd=3
                )
                btn.grid(row=r, column=c, padx=5, pady=5)
                btn.bind("<ButtonPress-1>", lambda e, x=cmd: self.on_mouse_press(x))
                btn.bind("<ButtonRelease-1>", lambda e, x=cmd: self.on_mouse_release(x))
                self.buttons[cmd] = btn

        info = tk.Label(
            self,
            text="Keyboard: W A S D or arrows",
            font=("Arial", 10),
            fg="gray",
            bg="#101820"
        )
        info.pack(pady=10)

    def bind_keys(self):
        self.bind("<KeyPress>", self.on_key_press)
        self.bind("<KeyRelease>", self.on_key_release)
        self.focus_set()

    def toggle_connection(self):
        if self.connected:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        try:
            self.serial_conn = serial.Serial(PORT, BAUD, timeout=1)
            time.sleep(1.5)
            self.connected = True
            self.status_label.config(text="CONNECTED", fg="lime")
            self.connect_btn.config(text="DISCONNECT", bg="orange")
        except Exception as e:
            messagebox.showerror("Connection error", str(e))

    def disconnect_serial(self):
        try:
            self.send_raw(b"S")
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
        except:
            pass

        self.connected = False
        self.serial_conn = None
        self.status_label.config(text="DISCONNECTED", fg="red")
        self.connect_btn.config(text="CONNECT", bg="green")

    def send_raw(self, data):
        if not self.connected or not self.serial_conn:
            return
        try:
            self.serial_conn.write(data)
            self.serial_conn.flush()
        except:
            self.disconnect_serial()

    def send_command(self, cmd):
        data = CMD.get(cmd, b"S")
        self.send_raw(data)
        self.last_cmd_label.config(text="Last command: " + cmd)

    def highlight_button(self, cmd, active):
        btn = self.buttons.get(cmd)
        if not btn:
            return

        if active:
            btn.config(bg="cyan", fg="black")
        else:
            btn.config(bg="#2a2a2a", fg="white")

    def on_mouse_press(self, cmd):
        self.active_mouse.add(cmd)
        self.highlight_button(cmd, True)
        self.send_command(cmd)

    def on_mouse_release(self, cmd):
        if cmd in self.active_mouse:
            self.active_mouse.remove(cmd)
        self.highlight_button(cmd, False)

        if not self.active_mouse and not self.pressed_keys:
            self.send_command("S")
            self.highlight_button("S", True)
            self.after(100, lambda: self.highlight_button("S", False))

    def on_key_press(self, event):
        key = event.keysym

        if key in self.pressed_keys:
            return

        cmd = KEY_MAP.get(key)
        if cmd:
            self.pressed_keys.add(key)
            self.highlight_button(cmd, True)
            self.send_command(cmd)

    def on_key_release(self, event):
        key = event.keysym
        cmd = KEY_MAP.get(key)

        if key in self.pressed_keys:
            self.pressed_keys.remove(key)

        if cmd:
            self.highlight_button(cmd, False)

        if not self.pressed_keys and not self.active_mouse:
            self.send_command("S")
            self.highlight_button("S", True)
            self.after(100, lambda: self.highlight_button("S", False))

    def on_close(self):
        self.disconnect_serial()
        self.destroy()


if __name__ == "__main__":
    app = RobotController()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
