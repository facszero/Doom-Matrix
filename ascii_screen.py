import time
import os
import json
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

# Caracteres ASCII para el doom.txt (oscuro → claro)
# CHARS = "@%#*+=-:. "
# CHARS = " .:-=+*#%@"
CHARS = " .:-=+*#%@ｱｲｳｴｵ"

# Paletas para frame.json (modo classic / matrix)
### CHARS_CLASSIC = list(" .:-=+*#%@")
### CHARS_CLASSIC = list(".:;-=+*#%@")
CHARS_CLASSIC = list(" .:-=+*#")
### CHARS_MATRIX  = list(" 0123456789ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄ")
CHARS_MATRIX  = list(".0123456789ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄ")

# REGION de captura (ajustar segun tu Doom en ventana)
'''
REGION = {
    "left": 2936,
    "top": 211,
    "width": 718,
    "height": 611
}
'''
REGION = {
    "left": 3000,
    "top": 100,
    "width": 718,
    "height": 611
}

# Resolucion ASCII final (también es el grid del JSON)
### ASCII_SIZE = (120, 60)  # (W, H)
### ASCII_SIZE = (180, 90)  # (W, H)
### ASCII_SIZE = (240, 120)  # (W, H)
ASCII_SIZE = (160, 80)  # (W, H)

# Archivos salida
OUT_TXT  = "doom.txt"
OUT_JSON = "frame.json"

# FPS aproximado
## FRAME_DELAY = 0.04
## FRAME_DELAY = 0.06
## FRAME_DELAY = 0.016 ## PARA 60 FPS
## FRAME_DELAY = 0.1 ## PARA 10 FPS
FRAME_DELAY = 0.12 ## 

# Títulos posibles de la ventana (ajustá si hace falta)
WINDOW_TITLE_KEYWORDS = ["doom", "chocolate"]  # busca por substring

# Si querés también redimensionar la ventana al tamaño de REGION
RESIZE_WINDOW_TO_REGION = True

# Cuánto esperar a que la ventana exista
WINDOW_WAIT_SECONDS = 10

# Detección “enemigos”: umbrales (ajustables)
## ENEMY_R_MIN = 140
ENEMY_R_MIN = 160
ENEMY_DR_G  = 50
ENEMY_DR_B  = 50

# Boost de brillo para enemigos (0..255)
ENEMY_GREEN_BOOST = 80


# ==========================
# FUNCIONES
# ==========================

def frame_to_ascii(gray_arr: np.ndarray) -> str:
    """
    Convierte matriz grayscale a texto ASCII usando CHARS (para doom.txt)
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


def write_atomic_bytes(path, bcontent: bytes):
    """
    Escritura atómica para JSON u otros binarios
    """
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(bcontent)
    os.replace(tmp, path)


def to_indices(gray: np.ndarray, n_chars: int) -> np.ndarray:
    """
    gray 0..255 -> índices 0..n_chars-1
    """
    return (gray.astype(np.uint16) * (n_chars - 1)) // 255


def green_intensity(gray: np.ndarray) -> np.ndarray:
    """
    Pseudo-depth: mapea brillo a intensidad de verde (50..255)
    Curva ajustable con exponente.
    """
    g = (gray.astype(np.float32) / 255.0)
    g = np.clip(g, 0, 1)
    ## g = g ** 1.4
    g = g ** 1.8
    return (50 + g * 205).astype(np.uint8)


def enemy_mask_from_rgb(rgb_small: np.ndarray) -> np.ndarray:
    """
    Máscara booleana: detecta zonas rojizas/naranjas típicas de enemigos.
    rgb_small: (H,W,3) uint8
    """
    r = rgb_small[..., 0].astype(np.int16)
    g = rgb_small[..., 1].astype(np.int16)
    b = rgb_small[..., 2].astype(np.int16)

    return (r > ENEMY_R_MIN) & ((r - g) > ENEMY_DR_G) & ((r - b) > ENEMY_DR_B)


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
        if win.isMinimized:
            win.restore()
            time.sleep(0.2)

        try:
            win.activate()
        except Exception:
            pass

        win.moveTo(REGION["left"], REGION["top"])
        time.sleep(0.1)

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
print("Grid ASCII_SIZE:", ASCII_SIZE)
print("Salida TXT:", OUT_TXT)
print("Salida JSON:", OUT_JSON)

move_and_resize_window_to_region()

print("Presiona CTRL+C para salir\n")

# ==========================
# LOOP PRINCIPAL
# ==========================

W, H = ASCII_SIZE  # (W,H)

with mss() as sct:
    while True:
        try:
            shot = sct.grab(REGION)

            # Convertir BGRA → RGB (PIL)
            img_rgb = Image.frombytes(
                "RGB",
                shot.size,
                shot.bgra,
                "raw",
                "BGRX"
            )

            # Reducir a grid (W,H)
            img_rgb_small = img_rgb.resize((W, H), Image.BILINEAR)
            rgb_small = np.array(img_rgb_small)  # (H,W,3)

            # Grayscale para ASCII
            img_gray_small = img_rgb_small.convert("L")
            gray = np.array(img_gray_small)      # (H,W)

            # 1) Doom clásico “simple” (doom.txt)
            ascii_img = frame_to_ascii(gray)
            write_atomic(OUT_TXT, ascii_img)

            # 2) Datos para Matrix/Classic en viewer (frame.json)
            enemy = enemy_mask_from_rgb(rgb_small)

            idx_classic = to_indices(gray, len(CHARS_CLASSIC))
            idx_matrix  = to_indices(gray, len(CHARS_MATRIX))

            g = green_intensity(gray)

            # Boost para enemigos: más neón
            if ENEMY_GREEN_BOOST > 0:
                g_enemy = np.clip(g.astype(np.int16) + ENEMY_GREEN_BOOST, 0, 255).astype(np.uint8)
                g = np.where(enemy, g_enemy, g)

            payload = {
                "w": W,
                "h": H,
                "classic": idx_classic.flatten().tolist(),
                "matrix":  idx_matrix.flatten().tolist(),
                "g":       g.flatten().tolist(),
                "enemy":   enemy.flatten().astype(int).tolist(),
                "ts": time.time()
            }

            jb = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            write_atomic_bytes(OUT_JSON, jb)

            time.sleep(FRAME_DELAY)

        except KeyboardInterrupt:
            print("\nFinalizado por usuario")
            break

        except Exception as e:
            print("Error:", e)
            time.sleep(1)
