from picamera2 import Picamera2
import cv2
import numpy as np

# ====== VALORES MANUALES HSV ======
# Cambia estos valores por los que obtengas
LOWER_HSV = np.array([10, 100, 100])
UPPER_HSV = np.array([25, 255, 255])

# Inicializar cámara
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

kernel = np.ones((5, 5), np.uint8)

while True:
    frame_rgb = picam2.capture_array()
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    frame_hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    # Generar máscara
    mask = cv2.inRange(frame_hsv, LOWER_HSV, UPPER_HSV)

    # Limpieza básica de ruido
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    cv2.imshow("Camara", frame_rgb)
    cv2.imshow("Mascara", mask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
