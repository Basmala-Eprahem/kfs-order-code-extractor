import os, sys
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
import cv2
from app.services.extractor import pick_orientation, _rot, _tokenize, _short_in_band

d = r"C:\Users\M lapan\Desktop\ocr\images"
g = cv2.imread(os.path.join(d, "1 (116).jpg"))
g = cv2.cvtColor(g, cv2.COLOR_BGR2GRAY)
ang = pick_orientation(g)
g = _rot(g, ang)
print("angle", ang)
g, toks = _tokenize(g)

numeric = [t for t in toks if t["txt"].isdigit() and len(t["txt"]) >= 4]
numeric.sort(key=lambda t: (t["top"], t["left"]))
for t in numeric:
    print(t["top"], t["left"], t["txt"], "w=%d h=%d" % (t["w"], t["h"]))

anch = [t for t in toks if t["txt"] in ("بيانات", "أبيقات", "ببانات", "بينات", "البيانات")]
print("anchors:", [(t["top"], t["left"], t["txt"]) for t in anch])
kod = [t for t in toks if t["txt"] in ("كود", "الكود", "قود", "گو")]
print("kods:", [(t["top"], t["left"], t["txt"]) for t in kod][:10])
talab = [t for t in toks if t["txt"] in ("الطلب", "الطلب.", "طلب", "الطب", "لطلب")]
print("talab:", [(t["top"], t["left"], t["txt"]) for t in talab][:10])