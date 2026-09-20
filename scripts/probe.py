"""Probe primary path internals for one image."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2
from app.services.extractor import (pick_orientation, _tokenize, KOD_WORDS,
                                    TALAB_WORDS, DIGIT_RE)

f = sys.argv[1]
img = cv2.imread(f)
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
ang = pick_orientation(g)
if ang == 90:
    g = cv2.rotate(g, cv2.ROTATE_90_CLOCKWISE)
elif ang == 180:
    g = cv2.rotate(g, cv2.ROTATE_180)
elif ang == 270:
    g = cv2.rotate(g, cv2.ROTATE_90_COUNTERCLOCKWISE)
g, toks = _tokenize(g)
print("angle", ang, "tokens", len(toks))
kods = [t for t in toks if t["txt"] in KOD_WORDS]
talabs = [t for t in toks if t["txt"] in TALAB_WORDS]
print("kods:", [(t['txt'], t['top'], t['left']) for t in kods])
print("talabs:", [(t['txt'], t['top'], t['left']) for t in talabs])
for t in sorted(toks, key=lambda z: z['top']):
    if DIGIT_RE.search(t['txt']) and len(t['txt']) >= 6:
        print("num", t['top'], t['left'], t['txt'])
for t in toks:
    if t['top'] >= 300 and t['top'] <= 360:
        print("row", t['top'], t['left'], t['txt'])