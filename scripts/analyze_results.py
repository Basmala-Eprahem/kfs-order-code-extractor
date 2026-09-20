import collections
import csv
import re

P = r"C:\Users\M lapan\Desktop\ocr\outputs\scan_all.csv"

rows = list(csv.DictReader(open(P, encoding="utf-8-sig")))

found = [r for r in rows if r["value"]]
none = [r for r in rows if not r["value"]]
print("total=%d found=%d none=%d" % (len(rows), len(found), len(none)))

lens = collections.Counter(len(r["value"]) for r in found)
print("value lengths:", dict(sorted(lens.items())))

fam = {}
for r in rows:
    n = r["filename"]
    if n.startswith("1 (") and n.endswith(").jpg"):
        k = "1(XX)"
    elif re.match(r"^\d+\.jpg$", n):
        k = "shortnum"
    elif n.lower().startswith("img"):
        k = "img2026"
    elif re.match(r"^\d{4,}\.jpg$", n):
        k = "4digit"
    elif n.startswith("000"):
        k = "000series"
    else:
        k = "other"
    fam.setdefault(k, [0, 0])
    fam[k][0] += 1
    if r["value"]:
        fam[k][1] += 1
for k, (t, f) in sorted(fam.items()):
    print("%-10s total=%4d found=%3d (%.0f%%)" % (k, t, f, 100.0 * f / max(1, t)))

val6 = [r for r in found if len(r["value"]) == 6 and r["value"].isdigit()]
print("6-digit values:", len(val6))
badsix = [r["value"] for r in found if len(r["value"]) != 6]
print("non-6-digit found count:", len(badsix), "unique:", sorted(set(badsix))[:15])

vals = sorted(int(r["value"]) for r in found if r["value"].isdigit())
if vals:
    print("min=%d max=%d" % (vals[0], vals[-1]))

by_method = collections.Counter(r["method"] for r in found)
print("method:", dict(by_method))

import os
out = [r for r in rows if r["filename"].startswith("1 (")][:5]
for r in out:
    print(r["filename"], r["value"], r["method"], r["orientation"])