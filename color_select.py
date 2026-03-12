from picamera2 import Picamera2
import cv2
import numpy as np

# Variables globales
selected_hsv = None
current_bgr = None
current_hsv = None

def nothing(x):
    pass

def mouse_callback(event, x, y, flags, param):
    global selected_hsv, current_hsv
    if event == cv2.EVENT_LBUTTONDOWN and current_hsv is not None:
        selected_hsv = current_hsv[y, x].copy()
        print(f"Color seleccionado HSV: H={selected_hsv[0]}, S={selected_hsv[1]}, V={selected_hsv[2]}")

def build_mask(hsv_img, hsv_ref, h_tol, s_tol, v_tol):
    h, s, v = int(hsv_ref[0]), int(hsv_ref[1]), int(hsv_ref[2])

    lower_s = max(0, s - s_tol)
    upper_s = min(255, s + s_tol)

    lower_v = max(0, v - v_tol)
    upper_v = min(255, v + v_tol)

    # Manejo especial para el canal H por el rango circular [0,179]
    h_low = h - h_tol
    h_high = h + h_tol

    if h_low < 0:
        lower1 = np.array([0, lower_s, lower_v], dtype=np.uint8)
        upper1 = np.array([h_high, upper_s, upper_v], dtype=np.uint8)

        lower2 = np.array([180 + h_low, lower_s, lower_v], dtype=np.uint8)
        upper2 = np.array([179, upper_s, upper_v], dtype=np.uint8)

        mask1 = cv2.inRange(hsv_img, lower1, upper1)
        mask2 = cv2.inRange(hsv_img, lower2, upper2)
        mask = cv2.bitwise_or(mask1, mask2)

    elif h_high > 179:
        lower1 = np.array([h_low, lower_s, lower_v], dtype=np.uint8)
        upper1 = np.array([179, upper_s, upper_v], dtype=np.uint8)

        lower2 = np.array([0, lower_s, lower_v], dtype=np.uint8)
        upper2 = np.array([h_high - 180, upper_s, upper_v], dtype=np.uint8)

        mask1 = cv2.inRange(hsv_img, lower1, upper1)
        mask2 = cv2.inRange(hsv_img, lower2, upper2)
        mask = cv2.bitwise_or(mask1, mask2)

    else:
        lower = np.array([h_low, lower_s, lower_v], dtype=np.uint8)
        upper = np.array([h_high, upper_s, upper_v], dtype=np.uint8)
        mask = cv2.inRange(hsv_img, lower, upper)

    # Limpieza básica de ruido
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return mask

# Inicializar cámara
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

# Ventanas y trackbars
cv2.namedWindow("Camara")
cv2.namedWindow("Mascara")
cv2.namedWindow("Controles")

cv2.setMouseCallback("Camara", mouse_callback)

cv2.createTrackbar("Tol H", "Controles", 10, 50, nothing)
cv2.createTrackbar("Tol S", "Controles", 50, 255, nothing)
cv2.createTrackbar("Tol V", "Controles", 50, 255, nothing)

print("Haz clic sobre un color en la ventana 'Camara'")
print("Tecla 'c' = borrar selección")
print("Tecla 'q' = salir")

while True:
    frame_rgb = picam2.capture_array()
    current_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    current_hsv = cv2.cvtColor(current_bgr, cv2.COLOR_BGR2HSV)

    display = frame_rgb.copy()

    if selected_hsv is not None:
        h_tol = cv2.getTrackbarPos("Tol H", "Controles")
        s_tol = cv2.getTrackbarPos("Tol S", "Controles")
        v_tol = cv2.getTrackbarPos("Tol V", "Controles")

        mask = build_mask(current_hsv, selected_hsv, h_tol, s_tol, v_tol)
        result = cv2.bitwise_and(frame_rgb,frame_rgb, mask=mask)

        texto = f"HSV sel: {selected_hsv[0]}, {selected_hsv[1]}, {selected_hsv[2]}"
        cv2.putText(display, texto, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Mascara", mask)
        cv2.imshow("Resultado", result)
    else:
        empty = np.zeros((480, 640), dtype=np.uint8)
        empty_bgr = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(display, "Haz clic sobre un color", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.imshow("Mascara", empty)
        cv2.imshow("Resultado", empty_bgr)

    cv2.imshow("Camara", display)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):
        selected_hsv = None
        print("Seleccion borrada")

cv2.destroyAllWindows()
