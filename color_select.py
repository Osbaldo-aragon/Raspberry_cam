from picamera2 import Picamera2
import cv2
import numpy as np

selected_hsv = None
frame_bgr = None

def nothing(x):
    pass

def mouse_callback(event, x, y, flags, param):
    global selected_hsv, frame_bgr
    if event == cv2.EVENT_LBUTTONDOWN and frame_bgr is not None:
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        selected_hsv = hsv[y, x].copy()
        print("HSV seleccionado:", selected_hsv)

def build_mask(hsv_img, hsv_ref, h_tol, s_tol, v_tol):
    h, s, v = map(int, hsv_ref)

    lower_s = max(0, s - s_tol)
    upper_s = min(255, s + s_tol)
    lower_v = max(0, v - v_tol)
    upper_v = min(255, v + v_tol)

    h_low = h - h_tol
    h_high = h + h_tol

    if h_low < 0:
        lower1 = np.array([0, lower_s, lower_v], dtype=np.uint8)
        upper1 = np.array([h_high, upper_s, upper_v], dtype=np.uint8)
        lower2 = np.array([180 + h_low, lower_s, lower_v], dtype=np.uint8)
        upper2 = np.array([179, upper_s, upper_v], dtype=np.uint8)
        mask = cv2.bitwise_or(
            cv2.inRange(hsv_img, lower1, upper1),
            cv2.inRange(hsv_img, lower2, upper2)
        )
    elif h_high > 179:
        lower1 = np.array([h_low, lower_s, lower_v], dtype=np.uint8)
        upper1 = np.array([179, upper_s, upper_v], dtype=np.uint8)
        lower2 = np.array([0, lower_s, lower_v], dtype=np.uint8)
        upper2 = np.array([h_high - 180, upper_s, upper_v], dtype=np.uint8)
        mask = cv2.bitwise_or(
            cv2.inRange(hsv_img, lower1, upper1),
            cv2.inRange(hsv_img, lower2, upper2)
        )
    else:
        lower = np.array([h_low, lower_s, lower_v], dtype=np.uint8)
        upper = np.array([h_high, upper_s, upper_v], dtype=np.uint8)
        mask = cv2.inRange(hsv_img, lower, upper)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask

picam2 = Picamera2()
picam2.configure(
    picam2.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )
)
picam2.start()

cv2.namedWindow("Camara")
cv2.namedWindow("Mascara")
cv2.namedWindow("Resultado")
cv2.namedWindow("Controles")

cv2.setMouseCallback("Camara", mouse_callback)

cv2.createTrackbar("Tol H", "Controles", 10, 50, nothing)
cv2.createTrackbar("Tol S", "Controles", 50, 255, nothing)
cv2.createTrackbar("Tol V", "Controles", 50, 255, nothing)

while True:
    frame_bgr = picam2.capture_array()   # ya está en el orden correcto para OpenCV
    display = frame_bgr.copy()

    if selected_hsv is not None:
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

        h_tol = cv2.getTrackbarPos("Tol H", "Controles")
        s_tol = cv2.getTrackbarPos("Tol S", "Controles")
        v_tol = cv2.getTrackbarPos("Tol V", "Controles")

        mask = build_mask(hsv, selected_hsv, h_tol, s_tol, v_tol)
        result = cv2.bitwise_and(frame_bgr, frame_bgr, mask=mask)

        cv2.imshow("Mascara", mask)
        cv2.imshow("Resultado", result)
    else:
        cv2.imshow("Mascara", np.zeros((480, 640), dtype=np.uint8))
        cv2.imshow("Resultado", np.zeros((480, 640, 3), dtype=np.uint8))

    cv2.imshow("Camara", display)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):
        selected_hsv = None

cv2.destroyAllWindows()
