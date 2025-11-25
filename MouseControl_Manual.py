import pyautogui
import time

# Desactivar failsafe
pyautogui.FAILSAFE = False

# Obtener tamaño de pantalla
screen_width, screen_height = pyautogui.size()

# Escala máxima asumida para coordenadas (ajustable)
# Suponemos un rango de trabajo de ±500 mm
max_mm_x = 500
max_mm_y = 500

# Estado de clics
left_clicking = False
right_clicking = False

def map_to_screen(x_mm, y_mm):
    # Forzamos el rango máximo a ±500 mm
    x_mm = max(-max_mm_x, min(max_mm_x, x_mm))
    y_mm = max(-max_mm_y, min(max_mm_y, y_mm))

    x_pixel = int((x_mm / max_mm_x) * (screen_width / 2)) + screen_width // 2
    y_pixel = int((-y_mm / max_mm_y) * (screen_height / 2)) + screen_height // 2

    # Clip a la pantalla con margen de seguridad
    safe_margin = 0
    x_pixel = max(safe_margin, min(screen_width - safe_margin, x_pixel))
    y_pixel = max(safe_margin, min(screen_height - safe_margin, y_pixel))
    return x_pixel, y_pixel

print("Introduce coordenadas en mm (x y z), escribe 'exit' para salir.")
print("Ejemplo: 100 200 50")

try:
    while True:
        line = input("> ")

        if line.strip().lower() == "exit":
            break

        try:
            x_mm, y_mm, z_mm = map(float, line.strip().split())
        except ValueError:
            print("Entrada inválida. Usa el formato: x y z")
            continue

        # Mapear coordenadas
        x_screen, y_screen = map_to_screen(x_mm, y_mm)
        pyautogui.moveTo(x_screen, y_screen)

        # Z -> Clicks
        if 0 <= z_mm < 380:
            if not left_clicking:
                pyautogui.mouseDown(button='left')
                left_clicking = True
                print("Clic izquierdo presionado")
        else:
            if left_clicking:
                pyautogui.mouseUp(button='left')
                left_clicking = False
                print("Clic izquierdo liberado")

        if 450 <= z_mm < 1500:
            if not right_clicking:
                pyautogui.mouseDown(button='right')
                right_clicking = True
                print("Clic derecho presionado")
        else:
            if right_clicking:
                pyautogui.mouseUp(button='right')
                right_clicking = False
                print("Clic derecho liberado")

except KeyboardInterrupt:
    print("\nInterrumpido por el usuario.")
