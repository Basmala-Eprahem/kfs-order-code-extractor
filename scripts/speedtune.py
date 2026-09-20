import os, sys, time
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
import cv2
from app.services.extractor import (pick_orientation, _rot, _tokenize,
                                    _label_short_pick, _band_short_pick, KOD_WORDS, TALAB_WORDS)

d = r"C:\Users\M lapan\Desktop\ocr\images"
fs = ["1 (6).jpg", "1 (38).jpg", "1 (116).jpg", "1 (10).jpg", "1 (102).jpg", "1 (124).jpg"]

def run(scale, top_frac):
    t0 = time.time()
    for n in fs:
        img = cv2.imread(os.path.join(d, n))
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ang = pick_orientation(g)
        g = _rot(g, ang)
        g, toks = _tokenize(g, scale=scale, top_frac=top_frac)
        kods = [t for t in toks if t["txt"] in KOD_WORDS]
        talabs = [t for t in toks if t["txt"] in TALAB_WORDS]
        v = _label_short_pick(kods, talabs, toks) or _band_short_pick(g, toks)
        print("  %-12s %s" % (n, v))
    print("scale=%d top=%.2f -> total %.1fs" % (scale, top_frac, time.time() - t0))

print("### scale 1200 top 0.62")
run(1200, 0.62)
print("### scale 1100 top 0.62")
run(1100, 0.62)
print("### scale 1400 top 0.50")
run(1400, 0.50)