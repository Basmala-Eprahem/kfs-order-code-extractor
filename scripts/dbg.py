"""Extraction debug: value + raw psm3 head for any image."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2, pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from app.services.extractor import pick_orientation

f = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\M lapan\Desktop\ocr\images\1 (102).jpg"
img = cv2.imread(f)
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
ang = pick_orientation(g)
print("chosen angle", ang)
if ang == 90:
    g = cv2.rotate(g, cv2.ROTATE_90_CLOCKWISE)
elif ang == 180:
    g = cv2.rotate(g, cv2.ROTATE_180)
elif ang == 270:
    g = cv2.rotate(g, cv2.ROTATE_90_COUNTERCLOCKWISE)
h, w = g.shape
sc = min(1.0, 1400 / max(h, w))
g = cv2.resize(g, (int(w*sc), int(h*sc))) if sc < 1.0 else g
txt = pytesseract.image_to_string(g, lang="ara+eng", config="--psm 3")
print(txt[:1200])