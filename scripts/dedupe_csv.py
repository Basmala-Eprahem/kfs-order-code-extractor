import csv
import sys

IN = r"C:\Users\M lapan\Desktop\ocr\outputs\scan_all.csv"

rows = {}
with open(IN, newline="", encoding="utf-8-sig") as fh:
    rd = csv.DictReader(fh)
    for r in rd:
        rows[r["filename"]] = r

with open(IN, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(r.keys()))
    w.writeheader()
    for name in sorted(rows):
        w.writerow(rows[name])

print("unique rows:", len(rows))