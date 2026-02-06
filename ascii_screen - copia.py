import time
import os
import numpy as np
from mss import mss
from PIL import Image

# --- mover ventana (Windows) ---
try:
    import pygetwindow as gw
except Exception:
    gw = None

# ==========================
# CONFIGURACION
# ==========================

# Caracteres ASCII (oscuro → claro)
# CHARS = "@%#*+=-:. "
# CHARS = " .:-=+*#%@"
CHARS = " .:-=+*#%@ｱｲｳｴｵ"



# REGION de captura (ajustar segun tu Doom en ventana)
REGION = {
    "left": 2936,
    "top": 211,
    "width": 718,
    "height": 611
}

# Resolucion ASCII final
ASCII_SIZE = (120, 60)

# Archivo salida
OUT_TXT = "doom.txt"

# FPS aproximado
FRAME_DELAY = 0.04

# Títulos posibles de la ventana (ajustá si hace falta)
WINDOW_TITLE_KEYWORDS = ["doom", "chocolate"]  # busca por substring

# Si querés también redimensionar la ventana al tamaño de REGION
RESIZE_WINDOW_TO_REGION = True

# Cuánto esperar a que la ventana exista
WINDOW_WAIT_SECONDS = 10


# ==========================
# FUNCIONES
# ==========================

def frame_to_ascii(gray_arr: np.ndarray) -> str:
    """
    Convierte matriz grayscale a texto ASCII
    """
    idx = (gray_arr.astype(np.uint16) * (len(CHARS) - 1)) // 255

    lines = [
        "".join(CHARS[i] for i in row)
        for row in idx
    ]

    return "\n".join(lines)


def write_atomic(path, content):
    """
    Escritura atomica para forzar refresh en visores
    """
    tmp = path + ".tmp"

    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)

    os.replace(tmp, path)


def find_doom_window():
    """
    Busca una ventana cuyo título contenga alguna keyword.
    Devuelve el objeto ventana o None.
    """
    if gw is None:
        return None

    wins = gw.getAllWindows()
    for w in wins:
        title = (w.title or "").lower()
        if any(k in title for k in WINDOW_TITLE_KEYWORDS):
            return w
    return None


def move_and_resize_window_to_region():
    """
    Intenta mover (y opcionalmente redimensionar) la ventana Doom
    a la posición/tamaño definidos por REGION.
    """
    if gw is None:
        print("Aviso: pygetwindow no está disponible. Saltando mover ventana.")
        return

    deadline = time.time() + WINDOW_WAIT_SECONDS
    win = None

    while time.time() < deadline and win is None:
        win = find_doom_window()
        if win is None:
            time.sleep(0.3)

    if win is None:
        print("Aviso: no se encontró ventana Doom/Chocolate Doom para mover.")
        print("Tip: ajustá WINDOW_TITLE_KEYWORDS según el título real de la ventana.")
        return

    try:
        # Restaurar si está minimizada
        if win.isMinimized:
            win.restore()
            time.sleep(0.2)

        # Traer al frente (a veces Windows lo bloquea, pero ayuda)
        try:
            win.activate()
        except Exception:
            pass

        # Mover
        win.moveTo(REGION["left"], REGION["top"])
        time.sleep(0.1)

        # Redimensionar (opcional)
        if RESIZE_WINDOW_TO_REGION:
            win.resizeTo(REGION["width"], REGION["height"])

        print(f"Ventana encontrada: '{win.title}'")
        print(f"Movida a: ({REGION['left']}, {REGION['top']})")
        if RESIZE_WINDOW_TO_REGION:
            print(f"Redimensionada a: {REGION['width']}x{REGION['height']}")

    except Exception as e:
        print("Aviso: error al mover/redimensionar ventana:", e)


# ==========================
# ARRANQUE
# ==========================

print("\nASCII SCREEN CAPTURE INICIADO")
print("Capturando REGION:", REGION)

# Intentar mover la ventana antes de capturar
move_and_resize_window_to_region()

print("Presiona CTRL+C para salir\n")

# ==========================
# LOOP PRINCIPAL
# ==========================

with mss() as sct:
    while True:
        try:
            shot = sct.grab(REGION)

            # Convertir BGRA → RGB
            img = Image.frombytes(
                "RGB",
                shot.size,
                shot.bgra,
                "raw",
                "BGRX"
            )

            # Convertir a grayscale + resize
            img = img.convert("L").resize(ASCII_SIZE)

            arr = np.array(img)

            ascii_img = frame_to_ascii(arr)

            write_atomic(OUT_TXT, ascii_img)

            time.sleep(FRAME_DELAY)

        except KeyboardInterrupt:
            print("\nFinalizado por usuario")
            break

        except Exception as e:
            print("Error:", e)
            time.sleep(1)
