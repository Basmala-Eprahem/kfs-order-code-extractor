import sys, glob
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
from app.services.batch import decode_bgr
from app.services.extractor import extract_value

for f in sorted(glob.glob(r"C:\Users\M lapan\Desktop\ocr\images\1 (6).jpg") +
                glob.glob(r"C:\Users\M lapan\Desktop\ocr\images\1 (38).jpg") +
                glob.glob(r"C:\Users\M lapan\Desktop\ocr\images\1 (10).jpg") +
                glob.glob(r"C:\Users\M lapan\Desktop\ocr\images\1 (116).jpg")):
    r = extract_value(decode_bgr(f))
    print(f.split("\\")[-1], "->", r["value"], r["method"])