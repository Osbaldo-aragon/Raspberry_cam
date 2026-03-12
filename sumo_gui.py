'''
sudo apt update
sudo apt install bluetooth bluez bluez-tools
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

bluetoothctl
power on
agent on
default-agent
scan on

pair AA:BB:CC:DD:EE:FF
trust AA:BB:CC:DD:EE:FF
info AA:BB:CC:DD:EE:FF
exit

sudo rfcomm release 0
sudo rfcomm bind 0 AA:BB:CC:DD:EE:FF
ls -l /dev/rfcomm0
ser = serial.Serial('/dev/rfcomm0', 9600, timeout=1)
'''
# -*- coding: utf-8 -*-
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
        self.geometry("800x400")
        self.resizable(False, False)
        self.configure(bg="#101820")

        self.serial_conn = None
        self.connected = False
        self.pressed_keys = set()
        self.active_mouse = set()

        self.build_ui()
        self.bind_keys()

    def build_ui(self):
        main = tk.Frame(self, bg="#101820")
        main.pack(fill="both", expand=True, padx=15, pady=15)

        left_panel = tk.Frame(main, bg="#101820", width=260)
        left_panel.pack(side="left", fill="y", padx=(0, 20))
        left_panel.pack_propagate(False)

        right_panel = tk.Frame(main, bg="#101820")
        right_panel.pack(side="left", fill="both", expand=True)

        title = tk.Label(
            left_panel,
            text="LLANERO CONTROL",
            font=("Arial", 16, "bold"),
            fg="cyan",
            bg="#101820"
        )
        title.pack(pady=(10, 15))

        self.status_label = tk.Label(
            left_panel,
            text="DISCONNECTED",
            font=("Arial", 12, "bold"),
            fg="red",
            bg="#101820"
        )
        self.status_label.pack(pady=5)

        port_label = tk.Label(
            left_panel,
            text="Port: " + PORT,
            font=("Arial", 11),
            fg="white",
            bg="#101820"
        )
        port_label.pack(pady=5)

        self.connect_btn = tk.Button(
            left_panel,
            text="CONNECT",
            font=("Arial", 11, "bold"),
            width=14,
            height=2,
            bg="green",
            fg="white",
            command=self.toggle_connection
        )
        self.connect_btn.pack(pady=(15, 10))

        self.stop_btn = tk.Button(
            left_panel,
            text="STOP",
            font=("Arial", 11, "bold"),
            width=14,
            height=2,
            bg="red",
            fg="white",
            command=lambda: self.send_command("S")
        )
        self.stop_btn.pack(pady=10)

        self.last_cmd_label = tk.Label(
            left_panel,
            text="Last command: None",
            font=("Arial", 12),
            fg="white",
            bg="#101820"
        )
        self.last_cmd_label.pack(pady=(20, 10))

        info = tk.Label(
            left_panel,
            text="Keyboard:\nW A S D or arrows",
            font=("Arial", 10),
            fg="gray",
            bg="#101820",
            justify="left"
        )
        info.pack(pady=10)

        pad_container = tk.Frame(right_panel, bg="#101820")
        pad_container.pack(expand=True)

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
                    pad_container,
                    text=label,
                    font=("Arial", 16, "bold"),
                    width=3,
                    height=1,
                    bg="#2a2a2a",
                    fg="white",
                    relief="raised",
                    bd=3,
                    padx=18,
                    pady=18
                )
                btn.grid(row=r, column=c, padx=8, pady=8)
                btn.bind("<ButtonPress-1>", lambda e, x=cmd: self.on_mouse_press(x))
                btn.bind("<ButtonRelease-1>", lambda e, x=cmd: self.on_mouse_release(x))
                self.buttons[cmd] = btn

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
