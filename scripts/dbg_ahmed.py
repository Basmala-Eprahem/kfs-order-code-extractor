import sys
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
import cv2
from app.services.batch import decode_bgr
from app.services.extractor import (pick_orientation, _rot, _tokenize, KOD_WORDS,
                                    TALAB_WORDS, DATA_ANCHOR_WORDS)


def dump(name, max_row=520):
    f = r"C:\Users\M lapan\Desktop\د احمد\\" + name
    img = decode_bgr(f)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ang = pick_orientation(g)
    g = _rot(g, ang)
    print("=" * 30, name, "angle", ang)
    g2, toks = _tokenize(g)
    labels = [t for t in toks if t["txt"] in KOD_WORDS + TALAB_WORDS + DATA_ANCHOR_WORDS]
    labels.sort(key=lambda t: (t["top"], t["left"]))
    print("-- labels:")
    for t in labels[:20]:
        print("   top=%d left=%d %s" % (t["top"], t["left"], t["txt"]))
    num = [t for t in toks if t["txt"].isdigit() and len(t["txt"]) >= 3 and t["top"] < 800]
    num.sort(key=lambda t: (t["top"], t["left"]))
    print("-- numbers (top<800):")
    for t in num[:40]:
        print("   top=%d left=%d %s (w=%d)" % (t["top"], t["left"], t["txt"], t["w"]))


for n in ("Scan_0002.jpg", "Scan_0003.jpg", "Scan_0005.jpg", "Scan_0008.jpg", "00000002.jpg"):
    dump(n)