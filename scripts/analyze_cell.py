import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2, pytesseract, numpy as np
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from app.services.extractor import pick_orientation, _rot, _tokenize, KOD_WORDS, TALAB_WORDS, DIGIT_RE

f = r"C:\Users\M lapan\Desktop\ocr\images\1 (10).jpg"
img = cv2.imread(f)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
ang = pick_orientation(gray)
print("orientation", ang)
g = _rot(gray, ang)
g, toks = _tokenize(g)

kods = [t for t in toks if t["txt"] in KOD_WORDS]
talabs = [t for t in toks if t["txt"] in TALAB_WORDS]
for w in kods + talabs:
    print(w["txt"], "top", w["top"], "left", w["left"], "w", w["w"], "h", w["h"])

vals = [t for t in toks if DIGIT_RE.fullmatch(t["txt"]) and len(t["txt"]) >= 9]
for v in vals:
    print("VAL", v["txt"], "top", v["top"], "left", v["left"], "w", v["w"], "h", v["h"])

# original res at rotated space
sc = min(1.0, 1400 / max(gray.shape))
print("scale", sc)
# map token bbox 2 to original-ish full-res rotated coords
for v in vals:
    x = int(v["left"] / sc); y = int(v["top"] / sc); w_v = int(v["w"] / sc); h_v = int(v["h"] / sc)
    print("fullres", v["txt"], "x", x, "y", y, "w", w_v, "h", h_v)