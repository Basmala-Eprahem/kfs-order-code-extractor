import os, sys, time
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
import cv2, numpy as np
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from app.services.extractor import pick_orientation, _rot, _label_short_pick, _band_short_pick, KOD_WORDS, TALAB_WORDS

d = r"C:\Users\M lapan\Desktop\ocr\images"
fs = ["1 (6).jpg", "1 (38).jpg", "1 (116).jpg", "1 (10).jpg", "1 (102).jpg", "1 (124).jpg"]
SCALE = 1400
TOP = 0.62

def toks_one(gray, psm):
    h, w = gray.shape
    sc = min(1.0, SCALE / max(h, w))
    gg = cv2.resize(gray, (int(w * sc), int(h * sc))) if sc < 1.0 else gray
    gg = gg[: int(gg.shape[0] * TOP), :]
    dump = pytesseract.image_to_data(gg, lang="ara+eng", config=f"--psm {psm}",
                                     output_type=pytesseract.Output.DICT)
    out = []
    for i in range(len(dump["text"])):
        t = dump["text"][i].strip()
        if not t or any(c in t for c in "/.,-:"):
            continue
        out.append({"txt": t, "left": dump["left"][i], "top": dump["top"][i],
                    "w": dump["width"][i], "h": dump["height"][i]})
    return out

for psm in (11, 11):
    print("### psm%d only" % psm)
    t0 = time.time()
    for n in fs:
        g = cv2.cvtColor(cv2.imread(os.path.join(d, n)), cv2.COLOR_BGR2GRAY)
        ang = pick_orientation(g)
        gg = _rot(g, ang)
        toks = toks_one(gg, psm)
        kods = [t for t in toks if t["txt"] in KOD_WORDS]
        talabs = [t for t in toks if t["txt"] in TALAB_WORDS]
        v = _label_short_pick(kods, talabs, toks) or _band_short_pick(gg, toks)
        print("  %-12s %s" % (n, v))
    print("total %.1fs" % (time.time() - t0))