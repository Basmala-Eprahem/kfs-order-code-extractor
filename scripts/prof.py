import os, sys, time
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from app.services.extractor import pick_orientation, _rot

g = cv2.imread(r"C:\Users\M lapan\Desktop\ocr\images\1 (6).jpg")
g = cv2.cvtColor(g, cv2.COLOR_BGR2GRAY)

t0 = time.time(); a = pick_orientation(g); print("orientation: %.1fs" % (time.time() - t0))
g = _rot(g, a)
t0 = time.time()
h, w = g.shape
sc = min(1.0, 1400 / max(h, w))
gg = cv2.resize(g, (int(w*sc), int(h*sc))) if sc < 1.0 else g
pytesseract.image_to_string(gg, lang="ara+eng", config="--psm 3")
print("psm3 full:  %.1fs" % (time.time() - t0))

t0 = time.time()
gg = cv2.resize(g, (int(w*sc), int(h*sc))) if sc < 1.0 else g
pytesseract.image_to_data(gg, lang="ara+eng", config="--psm 11", output_type=pytesseract.Output.DICT)
print("psm11 full: %.1fs" % (time.time() - t0))

t0 = time.time()
topcrop = gg[int(gg.shape[0]*0.05):int(gg.shape[0]*0.55), :]
pytesseract.image_to_data(topcrop, lang="ara+eng", config="--psm 11", output_type=pytesseract.Output.DICT)
print("psm11 top55%%: %.1fs" % (time.time() - t0))

t0 = time.time()
pytesseract.image_to_data(topcrop, lang="ara+eng", config="--psm 6", output_type=pytesseract.Output.DICT)
print("psm6 top55%%:  %.1fs" % (time.time() - t0))