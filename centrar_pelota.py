# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
import serial
import time
import cv2
import numpy as np
from picamera2 import Picamera2

PORT = "/dev/rfcomm0"
BAUD = 9600

CMD = {
    "L": b"L",
    "R": b"R",
    "S": b"S",
}

# Ajusta estos valores con el color de tu pelota
LOWER_HSV = np.array([92, 161, 142])
UPPER_HSV = np.array([112, 255, 242])

# Ajustes de deteccion
MIN_AREA = 1200
CENTER_TOL = 60

class RobotTracker(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Ball Tracker")
        self.geometry("320x220")
        self.resizable(False, False)
        self.configure(bg="#101820")

        self.serial_conn = None
        self.connected = False
        self.last_cmd = None

        self.build_ui()

        # Camara
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()

        self.kernel = np.ones((5, 5), np.uint8)

        self.running = True
        self.after(30, self.update_loop)

    def build_ui(self):
        title = tk.Label(
            self,
            text="BALL TRACKER",
            font=("Arial", 16, "bold"),
            fg="cyan",
            bg="#101820"
        )
        title.pack(pady=(15, 10))

        self.status_label = tk.Label(
            self,
            text="DISCONNECTED",
            font=("Arial", 12, "bold"),
            fg="red",
            bg="#101820"
        )
        self.status_label.pack(pady=5)

        self.connect_btn = tk.Button(
            self,
            text="CONNECT",
            font=("Arial", 11, "bold"),
            width=14,
            height=2,
            bg="green",
            fg="white",
            command=self.toggle_connection
        )
        self.connect_btn.pack(pady=10)

        self.cmd_label = tk.Label(
            self,
            text="Command: None",
            font=("Arial", 12),
            fg="white",
            bg="#101820"
        )
        self.cmd_label.pack(pady=5)

        self.pos_label = tk.Label(
            self,
            text="Ball: not detected",
            font=("Arial", 11),
            fg="white",
            bg="#101820"
        )
        self.pos_label.pack(pady=5)

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
            self.send_command("S")
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
        except:
            pass

        self.connected = False
        self.serial_conn = None
        self.last_cmd = None
        self.status_label.config(text="DISCONNECTED", fg="red")
        self.connect_btn.config(text="CONNECT", bg="green")
        self.cmd_label.config(text="Command: None")

    def send_raw(self, data):
        if not self.connected or not self.serial_conn:
            return
        try:
            self.serial_conn.write(data)
            self.serial_conn.flush()
        except:
            self.disconnect_serial()

    def send_command(self, cmd):
        if cmd == self.last_cmd:
            return

        data = CMD.get(cmd, b"S")
        self.send_raw(data)
        self.last_cmd = cmd
        self.cmd_label.config(text="Command: " + cmd)

    def process_frame(self, frame_rgb):
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        frame_hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(frame_hsv, LOWER_HSV, UPPER_HSV)

        # Limpieza de ruido
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)

        display = frame_rgb.copy()
        h, w, _ = display.shape
        center_x = w // 2
        left_limit = center_x - CENTER_TOL
        right_limit = center_x + CENTER_TOL

        cv2.line(display, (left_limit, 0), (left_limit, h), (255, 255, 0), 2)
        cv2.line(display, (right_limit, 0), (right_limit, h), (255, 255, 0), 2)
        cv2.line(display, (center_x, 0), (center_x, h), (0, 255, 255), 1)

        command = "S"
        ball_text = "Ball: not detected"

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)

            if area > MIN_AREA:
                x, y, bw, bh = cv2.boundingRect(largest)
                M = cv2.moments(largest)

                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])

                    cv2.rectangle(display, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
                    cv2.circle(display, (cx, cy), 6, (255, 0, 0), -1)

                    cv2.putText(display, f"X:{cx} Y:{cy}", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    ball_text = f"Ball: X={cx} Y={cy}"

                    if cx < left_limit:
                        command = "L"
                    elif cx > right_limit:
                        command = "R"
                    else:
                        command = "S"

        self.pos_label.config(text=ball_text)
        self.send_command(command)

        cv2.imshow("Camara", display)
        cv2.imshow("Mascara", mask)

    def update_loop(self):
        if not self.running:
            return

        try:
            frame_rgb = self.picam2.capture_array()
            self.process_frame(frame_rgb)
        except:
            pass

        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.on_close()
            return

        self.after(30, self.update_loop)

    def on_close(self):
        self.running = False
        try:
            self.send_command("S")
        except:
            pass

        try:
            self.disconnect_serial()
        except:
            pass

        try:
            cv2.destroyAllWindows()
        except:
            pass

        self.destroy()

if __name__ == "__main__":
    app = RobotTracker()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
