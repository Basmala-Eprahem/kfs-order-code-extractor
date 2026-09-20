import sys, cv2, pytesseract
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import config
from app.services.batch import decode_bgr
from app.services.extractor import pick_orientation, _rot, _tokenize, _cell_region

for name in ("Scan_0002.jpg", "Scan_0011.jpg", "Scan_0015.jpg"):
    f = r"C:\Users\M lapan\Desktop\د احمد\\" + name
    img = decode_bgr(f)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ang = pick_orientation(gray)
    g = _rot(gray, ang)
    gc, toks = _tokenize(g)
    print("=" * 60)
    print(name, "orig", gray.shape, "-> rot", ang, "->", g.shape)
    for t in toks:
        print("   top=%d left=%d w=%d h=%d  %r" % (t["top"], t["left"], t["w"], t["h"], t["txt"]))
    for t in toks:
        if any(ch.isdigit() for ch in t["txt"]) and not t["txt"][0:1].isalpha():
            cell = _cell_region(gc, t)
            if cell is None or cell.size == 0:
                continue
            big = cell if max(cell.shape) >= 60 else cv2.resize(cell, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
            reads = []
            for cfg in ("", "-c tessedit_char_whitelist=0123456789"):
                for psm in (6, 7, 8, 13):
                    try:
                        d = pytesseract.image_to_string(big, lang="eng", config="--psm %d %s" % (psm, cfg)).strip()
                    except pytesseract.TesseractError:
                        d = ""
                    reads.append(d.replace("\n", "/"))
            print("   cell %r psm67813 reads: %s" % (t["txt"], " | ".join(reads)))