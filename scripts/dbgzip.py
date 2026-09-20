import os, sys
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
from app.services import batch
import zipfile

# inspect the last produced zip
import glob
zips = sorted(glob.glob(r"C:\Users\M lapan\Desktop\ocr\outputs\batches\*.zip"))
print("zip count:", len(zips))
if zips:
    zf = zipfile.ZipFile(zips[-1])
    names = zf.namelist()
    print("entries:", len(names))
    for n in names:
        print("  ", repr(n))
    print("roots:", [n for n in names if "/" not in n])
    print("failed:", [n for n in names if n.startswith("failed")])