from PIL import Image
import numpy as np
import time

chars = "@%#*+=-:. "

def convertir_ascii(path_img, path_txt):
    img = Image.open(path_img).convert("L")
    img = img.resize((120, 60))

    pixels = np.array(img)

    ascii_img = "\n".join(
        "".join(chars[(int(p) * (len(chars)-1)) // 255] for p in row)
        for row in pixels
    )

    with open(path_txt, "w", encoding="utf-8") as f:
        f.write(ascii_img)

# LOOP
while True:
    convertir_ascii("frame.png", "doom.txt")
    time.sleep(0.2)  # 0.2 seg = ~5 FPS
