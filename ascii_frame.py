from PIL import Image
import numpy as np

chars = "@%#*+=-:. "  # de oscuro a claro

img = Image.open("frame.png").convert("L")
img = img.resize((120, 60))

pixels = np.array(img)

ascii_img = "\n".join(
    "".join(chars[(int(p) * (len(chars) - 1)) // 255] for p in row)
    for row in pixels
)

with open("doom.txt", "w", encoding="utf-8") as f:
    f.write(ascii_img)
