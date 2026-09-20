import sys, cv2, pytesseract
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

for n in ("1 (6).jpg", "1 (38).jpg", "1 (116).jpg", "1 (10).jpg", "1 (124).jpg", "1 (102).jpg"):
    g = cv2.imread(r"C:\Users\M lapan\Desktop\ocr\images\\" + n)
    g = cv2.cvtColor(g, cv2.COLOR_BGR2GRAY)
    try:
        d = pytesseract.image_to_osd(g)
        line = d.strip().splitlines()
        orient = script = rotate = None
        for l in line:
            if l.startswith("Orientation in degrees"):
                orient = l.split(":")[1].strip()
            elif l.startswith("Script"):
                script = l.split(":")[1].strip()
            elif l.startswith("Rotate"):
                rotate = l.split(":")[1].strip()
        print(n, "ori=%s script=%s rotate=%s" % (orient, script, rotate))
    except Exception as e:
        print(n, "OSD-ERR", e)