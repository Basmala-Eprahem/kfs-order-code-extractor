import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2, pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from app.services.extractor import pick_orientation, _rot

f = r"C:\Users\M lapan\Desktop\ocr\images\1 (6).jpg"
img = cv2.imread(f)
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
g = _rot(g, pick_orientation(g))
h, w = g.shape
sc = min(1.0, 1400 / max(h, w))
g = cv2.resize(g, (int(w*sc), int(h*sc))) if sc < 1.0 else g

band = g[270:370, 650:1350]
for fx in (2, 3, 4):
    up = cv2.resize(band, None, fx=fx, fy=fx, interpolation=cv2.INTER_CUBIC)
    for psm in (6, 7, 11):
        t = pytesseract.image_to_string(up, lang="ara+eng", config=f"--psm {psm}")
        tt = " | ".join(l for l in t.splitlines() if l.strip())
        if tt:
            print(f"x{fx} psm{psm}: {tt[:220]}")
    print("-")