import math
import re

import cv2
import numpy as np
import pytesseract

import config

pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

AR = re.compile(r"[\u0600-\u06FF]")

KEYWORDS = ("كود", "الطلب", "طلب", "بيانات", "قيد", "الارتفاع", "المخطط",
            "شهادة", "تسجيل", "المساحة", "المعلومات", "بيانات")

KOD_WORDS = ("كود", "الكود", "قود", "گو")
TALAB_WORDS = ("الطلب", "الطلب.", "طلب", "الطب", "لطلب", "الطالب", "الطلاب", "الطلث")
DATA_ANCHOR_WORDS = ("بيانات", "أبيقات", "ببانات", "بينات", "البيانات")

STRICT_NUM = re.compile(r"^\d{5,9}$")
LONG_NUM = re.compile(r"\d{10,}")
DIRTY_NUM = re.compile(r"[/\.,،\-:]")


def _hough_angle(gray):
    h, w = gray.shape
    sc = 640.0 / max(h, w)
    g = cv2.resize(gray, (int(w * sc), int(h * sc))) if sc < 1.0 else gray
    g = cv2.equalizeHist(g)
    edges = cv2.Canny(g, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, math.pi / 180, threshold=50,
                            minLineLength=24, maxLineGap=6)
    if lines is None:
        return None
    sx = sy = 0.0
    n = 0
    for l in lines:
        x1, y1, x2, y2 = np.asarray(l).reshape(4)
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length < 24:
            continue
        ang = math.atan2(dy, dx)
        sx += math.cos(2 * ang) * length
        sy += math.sin(2 * ang) * length
        n += 1
    if n < 12:
        return None
    mean = 0.5 * math.atan2(sy, sx)
    deg = math.degrees(mean) % 180
    return round(deg / 90.0) * 90.0


def _score_rot(g):
    txt = pytesseract.image_to_string(g, lang=config.OCR_LANGS, config="--psm 3")
    words = txt.split()
    ar = sum(1 for w in words if AR.search(w) and len(w) > 1)
    kw = sum(1 for w in words if w in KEYWORDS)
    return ar * 2 + kw * 8


def pick_orientation(gray):
    try:
        d = pytesseract.image_to_osd(gray)
        for l in d.splitlines():
            if l.startswith("Rotate:"):
                v = int(l.split(":")[1].strip())
                if v in (0, 90, 180, 270):
                    return v
    except pytesseract.TesseractError:
        pass
    return _hough_orientation(gray)


def _hough_orientation(gray):
    h, w = gray.shape
    sc = min(1.0, 700.0 / max(h, w))
    g = cv2.resize(gray, (int(w * sc), int(h * sc))) if sc < 1.0 else gray
    base = _hough_angle(gray)
    if base is None:
        best_ang, best = 0, -1
        for ang, rot in ((0, g),
                         (270, cv2.rotate(g, cv2.ROTATE_90_COUNTERCLOCKWISE)),
                         (180, cv2.rotate(g, cv2.ROTATE_180)),
                         (90, cv2.rotate(g, cv2.ROTATE_90_CLOCKWISE))):
            s = _score_rot(rot)
            if s > best:
                best_ang, best = ang, s
        return best_ang
    rot90 = cv2.rotate(g, cv2.ROTATE_90_CLOCKWISE)
    rot270 = cv2.rotate(g, cv2.ROTATE_90_COUNTERCLOCKWISE)
    s90 = _score_rot(rot90)
    s270 = _score_rot(rot270)
    return 270 if s270 >= s90 else 90


def _rot(gray, ang):
    if ang == 90:
        return cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
    if ang == 180:
        return cv2.rotate(gray, cv2.ROTATE_180)
    if ang == 270:
        return cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return gray


def _tokenize(gray, scale=1400, top_frac=0.62):
    h, w = gray.shape
    sc = min(1.0, scale / max(h, w))
    g = cv2.resize(gray, (int(w * sc), int(h * sc))) if sc < 1.0 else gray
    g = g[: int(g.shape[0] * top_frac), :]
    toks, seen = [], set()
    for psm in (11,):
        try:
            dump = pytesseract.image_to_data(g, lang=config.OCR_LANGS,
                                             config=f"--psm {psm}",
                                             output_type=pytesseract.Output.DICT)
        except pytesseract.TesseractError:
            continue
        for i in range(len(dump["text"])):
            t = dump["text"][i].strip()
            if not t or DIRTY_NUM.search(t):
                continue
            core = re.sub(r"[^\d]+$", "", re.sub(r"^[^\d]+", "", t))
            if len(core) >= 5 and core != t:
                t = core
            key = (t, dump["top"][i], dump["left"][i])
            if key in seen:
                continue
            seen.add(key)
            toks.append({"txt": t, "left": dump["left"][i], "top": dump["top"][i],
                         "w": dump["width"][i], "h": dump["height"][i]})
    return g, toks


def _short_in_band(toks, top, bot):
    out = []
    for t in toks:
        if not STRICT_NUM.match(t["txt"]):
            continue
        if t["top"] < top or t["top"] > bot:
            continue
        out.append(t)
    return out


def _cidx(t):
    return t["left"] + t["w"] / 2.0


def _label_short_pick(kods, talabs, toks):
    best = None
    for tlb in talabs:
        lh = tlb["h"]
        pairs = [k for k in kods if abs(k["top"] - tlb["top"]) <= lh * 1.1]
        if not pairs:
            continue
        kod = min(pairs, key=lambda k: abs(_cidx(k) - _cidx(tlb)))
        left = min(kod["left"], tlb["left"])
        right = max(kod["left"] + kod["w"], tlb["left"] + tlb["w"])
        top = min(kod["top"], tlb["top"])
        bot = max(kod["top"] + kod["h"], tlb["top"] + tlb["h"])
        lh = bot - top or lh
        label_cx = (left + right) / 2.0
        cands = [(abs(_cidx(t) - label_cx), t)
                 for t in _short_in_band(toks, top - lh * 1.5, bot + lh * 3)
                 if t["left"] + t["w"] < right + 1]
        if not cands:
            cands = [(abs(_cidx(t) - label_cx), t)
                     for t in _short_in_band(toks, top - lh * 1.5, bot + lh * 3)]
        cands.sort(key=lambda z: z[0])
        if cands:
            best = cands[0][1]["txt"]
    return best


SIX_MARGIN = 40


def _band_short_pick(toks):
    anchors = [t for t in toks if t["txt"] in DATA_ANCHOR_WORDS]
    if not anchors:
        return None, None
    a = min(anchors, key=lambda t: t["top"])
    row_h = max(t["h"] for t in anchors)
    top = max(0, a["top"] - row_h)
    bot = a["top"] + row_h * 5
    longs = [t for t in toks if LONG_NUM.search(t["txt"])
             and top - row_h <= t["top"] <= bot + row_h]
    if not longs:
        return None, None
    min_long_left = min(t["left"] for t in longs)
    shorts = [t for t in _short_in_band(toks, top, bot)
              if t["left"] + t["w"] < min_long_left]
    if not shorts:
        return None, None
    shorts.sort(key=lambda t: t["left"])
    return shorts[-1], "band"


def _structural_short_pick(toks):
    longs = [t for t in toks if LONG_NUM.search(t["txt"])]
    if longs:
        srt = sorted(longs, key=lambda t: t["top"])
        top = max(0, srt[0]["top"] - SIX_MARGIN)
        bot = max(t["top"] + t["h"] for t in longs) + SIX_MARGIN
        min_long_left = min(t["left"] for t in longs)
        shorts = [t for t in _short_in_band(toks, top, bot)
                  if t["left"] + t["w"] < min_long_left]
        if shorts:
            six = [t for t in shorts if len(t["txt"]) == 6]
            pool = six or shorts
            pool.sort(key=lambda t: t["left"])
            return pool[-1], "structural"
    anchors = [t for t in toks
               if t["txt"] in DATA_ANCHOR_WORDS or t["txt"] in TALAB_WORDS]
    if anchors:
        a = min(anchors, key=lambda t: t["top"])
        row_h = max(t["h"] for t in anchors)
        top = max(0, a["top"] - row_h)
        bot = a["top"] + row_h * 5
        shorts = _short_in_band(toks, top, bot)
        six = [t for t in shorts if len(t["txt"]) == 6]
        if six:
            six.sort(key=lambda t: t["left"])
            return six[-1], "structural"
        if len(shorts) == 1:
            return shorts[0], "structural"
    return None, None


def _cell_variants(gray, tok):
    pad = max(8, int(tok["h"] * 0.6))
    x0 = max(0, tok["left"] - pad)
    y0 = max(0, tok["top"] - pad // 2)
    x1 = tok["left"] + tok["w"] + pad
    y1 = tok["top"] + tok["h"] + pad
    cell = gray[y0:y1, x0:x1]
    if cell.size == 0:
        return []
    outs = [cell]
    _, th = cv2.threshold(cell, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    outs.append(th)
    ad = cv2.adaptiveThreshold(cell, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY, 51, 15)
    outs.append(ad)
    grown = []
    for c in outs:
        if max(c.shape) < 140:
            grown.append(cv2.resize(c, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC))
        else:
            grown.append(c)
    return grown


def _recover_six(gray, tok):
    votes = {}
    for v in _cell_variants(gray, tok):
        for psm in (6, 7, 8, 13):
            try:
                t = pytesseract.image_to_string(
                    v, lang="eng",
                    config=f"--psm {psm} -c tessedit_char_whitelist=0123456789")
                d = re.sub(r"\D", "", t)
            except pytesseract.TesseractError:
                continue
            if len(d) == 6:
                votes[d] = votes.get(d, 0) + 1
    if not votes:
        return None
    best, c = max(votes.items(), key=lambda kv: kv[1])
    if c >= 2 and len(best) == 6:
        return best
    return None


def extract_value(img_bgr):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    ang = pick_orientation(gray)
    g = _rot(gray, ang)
    g, toks = _tokenize(g)

    kods = [t for t in toks if t["txt"] in KOD_WORDS]
    talabs = [t for t in toks if t["txt"] in TALAB_WORDS]

    v = _label_short_pick(kods, talabs, toks)
    if v:
        return {"orientation": ang, "label": "كود الطلب", "value": v, "method": "label"}
    tok, method = _band_short_pick(toks)
    if tok is None:
        tok, method = _structural_short_pick(toks)
    if tok is None:
        return {"orientation": ang, "label": None, "value": None, "method": None}
    v = tok["txt"]
    if len(re.sub(r"\D", "", v)) != 6:
        rec = _recover_six(g, tok)
        if rec:
            v = rec
    return {"orientation": ang, "label": "كود الطلب", "value": v, "method": method}