import sys
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from app.services.batch import decode_bgr
from app.services.extractor import pick_orientation, _rot

f = r"C:\Users\M lapan\Desktop\د احمد\Scan_0002.jpg"
img = decode_bgr(f)
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
g = _rot(g, pick_orientation(g))
h, w = g.shape
sc = 2400 / max(h, w)
g2 = cv2.resize(g, (int(w * sc), int(h * sc)))
print("shape after scale:", g2.shape, "orig", (h, w))
d = pytesseract.image_to_data(g2, lang="ara+eng", config="--psm 11",
                              output_type=pytesseract.Output.DICT)
for i in range(len(d["text"])):
    t = d["text"][i].strip()
    if t and any(ch.isdigit() for ch in t):
        x, y, ww, hh = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
        if 0.05 < (y + hh / 2) / g2.shape[0] < 0.6:
            print("top=%d left=%d w=%d h=%d  %s" % (y, x, ww, hh, t))