import numpy as np
import cv2
import json
import paho.mqtt.client as mqtt
import threading
import time
import keyboard
import ctypes
from ctypes import wintypes

# ===============================================================
# --- RATÓN CON CTYPES (SendInput) ---
# ===============================================================
PUL = ctypes.POINTER(ctypes.c_ulong)

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL))

class INPUT(ctypes.Structure):
    _fields_ = (("type", ctypes.c_ulong),
                ("mi", MOUSEINPUT))

# Constantes de eventos
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

# Dimensiones de pantalla
user32 = ctypes.WinDLL('user32', use_last_error=True)
screen_w = user32.GetSystemMetrics(0)
screen_h = user32.GetSystemMetrics(1)

# ---------------------------------------------------------------
# Mueve el mouse a posición absoluta en pantalla
def move_mouse(x, y):
    x = int(x * 65535 / screen_w)
    y = int(y * 65535 / screen_h)
    mi = MOUSEINPUT(x, y, 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, None)
    ctypes.windll.user32.SendInput(1, ctypes.byref(INPUT(type=0, mi=mi)), ctypes.sizeof(INPUT))

# ---------------------------------------------------------------
# Clic izquierdo
def left_down():
    mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, None)
    ctypes.windll.user32.SendInput(1, ctypes.byref(INPUT(type=0, mi=mi)), ctypes.sizeof(INPUT))

def left_up():
    mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, None)
    ctypes.windll.user32.SendInput(1, ctypes.byref(INPUT(type=0, mi=mi)), ctypes.sizeof(INPUT))

# ---------------------------------------------------------------
# Clic derecho
def right_down():
    mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_RIGHTDOWN, 0, None)
    ctypes.windll.user32.SendInput(1, ctypes.byref(INPUT(type=0, mi=mi)), ctypes.sizeof(INPUT))

def right_up():
    mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_RIGHTUP, 0, None)
    ctypes.windll.user32.SendInput(1, ctypes.byref(INPUT(type=0, mi=mi)), ctypes.sizeof(INPUT))


# ===============================================================
# --- CONFIGURACIÓN MQTT ---
# ===============================================================
BROKER = "192.168.50.200"
PORT = 1880
TOPIC = "mocap/all"
TARGET_ID = "69"

exit_program = False
esc_pressed_time = None

# ===============================================================
# --- VARIABLES GLOBALES ---
# ===============================================================
x = 0.0
y = 0.0
z = 0.0
new_data = False

left_clicking = False
right_clicking = False

# ===============================================================
# --- CALLBACKS MQTT ---
# ===============================================================
def on_connect(client, userdata, flags, rc):
    print("Conectado con código:", rc)
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    global x, y, z, new_data
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        identifier = data.get("identifier")
        if identifier != TARGET_ID:
            return

        pos = data["payload"]["pose"]["position"]
        x, y, z = pos["x"] * 1000, pos["y"] * 1000, pos["z"] * 1000
        new_data = True

    except Exception as e:
        print("Error al procesar mensaje:", e)

# ===============================================================
# --- INICIAR CLIENTE MQTT EN HILO ---
# ===============================================================
def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()

mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
mqtt_thread.start()

# ===============================================================
# --- DEFINIR PLANOS Y HOMOGRAFÍA ---
# ===============================================================
A = np.array([-853, -1583])
B = np.array([854, -1583])
C = np.array([854, 1475])
D = np.array([-853, 1475])

width = 870 #850 #1707 para 1 stream
height = 1696 #1470 #3058 para 1 stream

if width < height and screen_w > screen_h:
    print("Rotando segundo plano 90° para coincidir con la orientación de la pantalla...")
    width, height = height, width
    rect_local = np.array([
        [-width/2, -height/2],
        [ width/2, -height/2],
        [ width/2,  height/2],
        [-width/2,  height/2]
    ])
    R90 = np.array([[0, -1], [1, 0]])
    rect_local = rect_local @ R90.T
else:
    rect_local = np.array([
        [-width/2, -height/2],
        [ width/2, -height/2],
        [ width/2,  height/2],
        [-width/2,  height/2]
    ])

center = np.array([-410, -54])
scale = 1
angle_deg = 180
theta = np.deg2rad(angle_deg)
R = np.array([[np.cos(theta), -np.sin(theta)],
              [np.sin(theta),  np.cos(theta)]])
rect_transformed = center + scale * (rect_local @ R.T)

half_w, half_h = screen_w/2, screen_h/2
third_plane = np.array([
    [-half_w, -half_h],
    [ half_w, -half_h],
    [ half_w,  half_h],
    [-half_w,  half_h]
], dtype=np.float32)

src_points = rect_transformed.astype(np.float32)
dst_points = third_plane
H, _ = cv2.findHomography(src_points, dst_points)

# ===============================================================
# --- FUNCIÓN DE MAPEO DE COORDENADAS ---
# ===============================================================
def map_to_screen_from_marker(x_mm, y_mm):
    point = np.array([[x_mm, y_mm]], dtype=np.float32)
    point_hom = cv2.perspectiveTransform(np.array([point]), H)[0][0]

    screen_x = int(point_hom[0] + screen_w / 2)
    screen_y = int(-point_hom[1] + screen_h / 2)

    screen_x = max(0, min(screen_w - 1, screen_x))
    screen_y = max(0, min(screen_h - 1, screen_y))
    return screen_x, screen_y

# ===============================================================
# --- FUNCIÓN PARA DETENER EL PROGRAMA ---
# ===============================================================
def esc_monitor():
    global exit_program, esc_pressed_time
    while not exit_program:
        if keyboard.is_pressed('esc'):
            if esc_pressed_time is None:
                esc_pressed_time = time.time()
            elif time.time() - esc_pressed_time >= 4:
                print("Tecla ESC mantenida 5 segundos. Saliendo...")
                exit_program = True
        else:
            esc_pressed_time = None
        time.sleep(0.1)

threading.Thread(target=esc_monitor, daemon=True).start()

# ===============================================================
# --- LOOP PRINCIPAL ---
# ===============================================================
try:
    print("Control de mouse activo. Mueve el marcador para mover el cursor.")
    while not exit_program:
        if new_data:
            new_data = False

        x_screen, y_screen = map_to_screen_from_marker(x, y)
        move_mouse(x_screen, y_screen)

        # Control de clic izquierdo
        if 0 <= z < 100:
            if not left_clicking:
                left_down()
                left_clicking = True
        else:
            if left_clicking:
                left_up()
                left_clicking = False

        # Control de clic derecho
        if 300 <= z < 1500:
            if not right_clicking:
                right_down()
                right_clicking = True
        else:
            if right_clicking:
                right_up()
                right_clicking = False

        time.sleep(0.005)  # 200 Hz aprox

except KeyboardInterrupt:
    print("\nInterrumpido por el usuario.")

print("Programa finalizado correctamente.")
