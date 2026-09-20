import sys, os, re, glob, time
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
from app.services.batch import decode_bgr
from app.services.extractor import extract_value

files = sorted(glob.glob(r"C:\Users\M lapan\Desktop\د احمد\*.jpg"))
CODE_RE = re.compile(r"^\d{6}$")
t0 = time.time()
ok = fail = 0
for i, f in enumerate(files, 1):
    t = time.time()
    img = decode_bgr(f)
    if img is None:
        print("READ-FAIL", os.path.basename(f)); fail += 1; continue
    r = extract_value(img)
    v = r.get("value")
    good = bool(v and CODE_RE.match(v))
    ok += good; fail += not good
    print("%s -> %s [%s] %s  (%.1fs)" % (
        os.path.basename(f), v, r.get("method"), "OK" if good
        else r.get("orientation"), time.time() - t))
print("\nTOTAL %d files: OK=%d FAIL=%d  %.1fs total" % (len(files), ok, fail, time.time() - t0))