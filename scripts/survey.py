"""Survey families: does doc contain بيانات الطلب / 0150-code at auto orientation."""
import sys, os, glob, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2, pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from app.services.extractor import pick_orientation

def rot(g, ang):
    if ang == 90: return cv2.rotate(g, cv2.ROTATE_90_CLOCKWISE)
    if ang == 180: return cv2.rotate(g, cv2.ROTATE_180)
    if ang == 270: return cv2.rotate(g, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return g

files = sorted(glob.glob(r"C:\Users\M lapan\Desktop\ocr\images\*.jpg"))
# pick spread sample by name family
import collections
fam = collections.defaultdict(list)
for f in files:
    b = os.path.basename(f)
    if b.startswith("000000"): k = "000000"
    elif re.match(r"^\d{4,}\.", b): k = "0000"
    elif b.startswith("1 ("): k = "1(family)"
    elif b.startswith("img2026"): k = "img2026"
    else: k = "other"
    fam[k].append(f)

sample = []
for k, fl in fam.items():
    step = max(1, len(fl) // 12)
    sample.extend(fl[::step][:12])

p015 = re.compile(r"015\d{10,}")
pdata = re.compile(r"بيانات\s*الطلب|الطل[بث].")
for f in sample[:80]:
    g = cv2.cvtColor(cv2.imread(f), cv2.COLOR_BGR2GRAY)
    h, w = g.shape
    sc = min(1.0, 1000 / max(h, w))
    if sc < 1.0:
        g = cv2.resize(g, (int(w*sc), int(h*sc)))
    ang = pick_orientation(g)
    g = rot(g, ang)
    txt = pytesseract.image_to_string(g, lang="ara+eng", config="--psm 3")
    has015 = bool(p015.search(txt))
    hasdata = bool(pdata.search(txt))
    print(f"{os.path.basename(f):>28} ang={ang:>3} data={hasdata} 015={has015}")