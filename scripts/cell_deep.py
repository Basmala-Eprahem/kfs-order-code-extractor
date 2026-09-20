import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2, pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from app.services.extractor import pick_orientation, _rot

f = r"C:\Users\M lapan\Desktop\ocr\images\1 (10).jpg"
img = cv2.imread(f)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
ang = pick_orientation(gray)
g = _rot(gray, ang) if ang else gray

x0, x1, y0, y1 = 1640, 1880, 495, 555
cell = g[y0:y1, x0:x1]

for name, proc in (("gray", cell), ("inv", 255 - cell)):
    for fx in (2, 3, 4, 5):
        up = cv2.resize(proc, None, fx=fx, fy=fx, interpolation=cv2.INTER_CUBIC)
        for psm in (7, 13):
            try:
                t = pytesseract.image_to_string(up, lang="eng",
                                                config=f"--psm {psm} -c tessedit_char_whitelist=0123456789").strip()
            except pytesseract.TesseractError:
                t = ""
            if t:
                print(f"{name} x{fx} psm{psm}: {t}")

def ascii_art(graypic, ch_w):
    h, w = graycopy.shape[:2] if False else graypic.shape
    target_h = 40
    ah = max(1, h // target_h)
    aw = max(1, ch_w)
    for yy in range(0, h, ah):
        row = []
        for xx in range(0, w, aw):
            blk = graypic[yy:yy + ah, xx:xx + aw]
            darks = float((blk < 128).mean())
            row.append("#" if darks > 0.5 else ("+" if darks > 0.2 else ("." if darks > 0.05 else " ")))
        print("".join(row))

# upscale cell for visible ascii
up = cv2.resize(cell, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
print("=== ASCII of cell (6x) ===")
ascii_art(up, 6)
up_i = cv2.resize(255 - cell, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
print("=== ASCII inverted (6x) ===")
ascii_art(up_i, 6)