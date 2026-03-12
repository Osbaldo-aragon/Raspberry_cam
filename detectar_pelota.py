# -*- coding: utf-8 -*-
from picamera2 import Picamera2
import cv2
import numpy as np

# Rangos HSV manuales
LOWER_HSV = np.array([92, 161, 142])
UPPER_HSV = np.array([112, 255, 242])

# Area minima para ignorar ruido pequeno
MIN_AREA = 800

# Inicializar camara
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

kernel = np.ones((5, 5), np.uint8)

while True:
    # Captura
    frame_rgb = picam2.capture_array()
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    frame_hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    # Mascara por color
    mask = cv2.inRange(frame_hsv, LOWER_HSV, UPPER_HSV)

    # Limpieza de ruido
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.GaussianBlur(mask, (5, 5), 0)

    # Copia para dibujar
    display = frame_rgb.copy()

    # Buscar contornos
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Tomar el contorno de mayor area
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)

        if area > MIN_AREA:
            # Bounding box
            x, y, w, h = cv2.boundingRect(largest)
            cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Centroide
            M = cv2.moments(largest)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # Dibujar centro
                cv2.circle(display, (cx, cy), 6, (0, 0, 255), -1)

                # Mostrar coordenadas
                texto = f"X:{cx} Y:{cy}"
                cv2.putText(display, texto, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Camara", display)
    cv2.imshow("Mascara", mask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
