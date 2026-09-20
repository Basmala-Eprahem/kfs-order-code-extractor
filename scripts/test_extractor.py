"""Test extract_value across filename families."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2
from app.services.extractor import extract_value

files = [r"C:\Users\M lapan\Desktop\ocr\images\1 (10).jpg",
         r"C:\Users\M lapan\Desktop\ocr\images\1 (100).jpg",
         r"C:\Users\M lapan\Desktop\ocr\images\1 (101).jpg",
         r"C:\Users\M lapan\Desktop\ocr\images\1 (102).jpg",
         r"C:\Users\M lapan\Desktop\ocr\images\1 (103).jpg",
         r"C:\Users\M lapan\Desktop\ocr\images\1 (104).jpg",
         r"C:\Users\M lapan\Desktop\ocr\images\1 (105).jpg",
         r"C:\Users\M lapan\Desktop\ocr\images\1 (660).jpg",
         r"C:\Users\M lapan\Desktop\ocr\images\00000001.jpg",
         r"C:\Users\M lapan\Desktop\ocr\images\00000048.jpg",
         r"C:\Users\M lapan\Desktop\ocr\images\004.jpg",
         r"C:\Users\M lapan\Desktop\ocr\images\img20260826_10483430.jpg"]
for f in files:
    if not os.path.exists(f):
        print(os.path.basename(f), "MISSING")
        continue
    img = cv2.imread(f)
    if img is None:
        print(os.path.basename(f), "CORRUPT")
        continue
    r = extract_value(img)
    print(f"{os.path.basename(f):>28} orient={r['orientation']:>4} label={str(r['label']):>22} value={r['value']}")