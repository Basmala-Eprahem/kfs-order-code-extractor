import sys, re, cv2, pytesseract
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from app.services.batch import decode_bgr
from app.services.extractor import pick_orientation, _rot, _tokenize, _cell_variants

f = r"C:\Users\M lapan\Desktop\د احمد\Scan_0002.jpg"
img = decode_bgr(f)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
ang = pick_orientation(gray)
g = _rot(gray, ang)
gc, toks = _tokenize(g)
tok = [t for t in toks if t["txt"] == "00077"][0]
print("token:", tok)
for vi, v in enumerate(_cell_variants(gc, tok)):
    print("variant", vi, v.shape)
    for psm in (3, 6, 7, 8, 13):
        for wh in ("0123456789", ""):
            t = pytesseract.image_to_string(v, lang="eng", config="--psm %d%s" % (psm, " -c tessedit_char_whitelist=" + wh if wh else "")).strip()
            if t:
                print("   psm%d wh=%s -> %r" % (psm, wh or "all", t))