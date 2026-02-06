import time
import ctypes

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_mouse_pos():
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

print("\n=== MEDIDOR DE REGION PARA CAPTURA ===\n")

print("Mové el mouse a la esquina SUPERIOR IZQUIERDA del Doom...")
for i in range(5, 0, -1):
    print(f"{i}...")
    time.sleep(1)

x1, y1 = get_mouse_pos()
print(f"Top-Left capturado: {x1}, {y1}\n")

print("Mové el mouse a la esquina INFERIOR DERECHA del Doom...")
for i in range(5, 0, -1):
    print(f"{i}...")
    time.sleep(1)

x2, y2 = get_mouse_pos()
print(f"Bottom-Right capturado: {x2}, {y2}\n")

width = x2 - x1
height = y2 - y1

print("=====================================")
print("REGION sugerida:")
print(f'REGION = {{"left": {x1}, "top": {y1}, "width": {width}, "height": {height}}}')
print("=====================================")
