import sys, cv2
sys.path.insert(0, r"C:\Users\M lapan\Desktop\ocr")
from app.services.extractor import _score_rot, _hough_angle

for n in ("1 (6).jpg", "1 (38).jpg", "1 (116).jpg", "1 (10).jpg", "1 (124).jpg", "1 (102).jpg"):
    g = cv2.imread(r"C:\Users\M lapan\Desktop\ocr\images\\" + n)
    g = cv2.cvtColor(g, cv2.COLOR_BGR2GRAY)
    h, w = g.shape
    sc = min(1.0, 700.0 / max(h, w))
    gg = cv2.resize(g, (int(w * sc), int(h * sc))) if sc < 1.0 else g
    print(n, "hough=", _hough_angle(g),
          "s0=%d" % _score_rot(gg),
          "s180=%d" % _score_rot(cv2.rotate(gg, cv2.ROTATE_180)),
          "s90=%d" % _score_rot(cv2.rotate(gg, cv2.ROTATE_90_CLOCKWISE)),
          "s270=%d" % _score_rot(cv2.rotate(gg, cv2.ROTATE_90_COUNTERCLOCKWISE)))