import os, sys, time
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
import cv2
from app.services.extractor import extract_value

d = r"C:\Users\M lapan\Desktop\ocr\images"
fs = sorted(f for f in os.listdir(d) if f.startswith("1 (") and f.endswith(".jpg"))[:30]
t0 = time.time()
for n in fs:
    r = extract_value(cv2.imread(os.path.join(d, n)))
    print("%-16s %-12s %s" % (n, str(r["value"]), r["method"] or "-"))
print("elapsed %.1fs" % (time.time() - t0))