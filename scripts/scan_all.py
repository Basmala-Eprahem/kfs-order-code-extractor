import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2

import config
from app.services.extractor import extract_value

DATASET = config.DATASET_DIR
OUT_CSV = os.path.join(config.OUTPUT_DIR, "scan_all.csv")
PROGRESS = os.path.join(config.OUTPUT_DIR, "scan_all_progress.txt")

ROWS = ["filename", "orientation", "label", "method", "value", "processing_ms"]


def done_set():
    if not os.path.exists(OUT_CSV):
        return set()
    with open(OUT_CSV, newline="", encoding="utf-8-sig") as fh:
        return {r["filename"] for r in csv.DictReader(fh)}


def main():
    files = sorted(f for f in os.listdir(DATASET)
                   if f.lower().endswith((".jpg", ".jpeg", ".png")))
    done = done_set()
    todo = [f for f in files if f not in done]
    total = len(files)

    with open(OUT_CSV, "a", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=ROWS)
        if not done:
            writer.writeheader()
        found = none_count = 0
        t0 = time.time()
        for i, name in enumerate(todo, 1):
            img = cv2.imread(os.path.join(DATASET, name))
            if img is None:
                writer.writerow({"filename": name, "processing_ms": "corrupt"})
                continue
            s = time.time()
            try:
                r = extract_value(img)
            except Exception as e:
                r = {"orientation": None, "label": None, "value": None,
                     "method": "error:%s" % e}
            ms = int((time.time() - s) * 1000)
            writer.writerow({
                "filename": name,
                "orientation": r.get("orientation"),
                "label": r.get("label"),
                "method": r.get("method"),
                "value": r.get("value"),
                "processing_ms": ms,
            })
            fh.flush()
            if r.get("value"):
                found += 1
            else:
                none_count += 1
            if i % 10 == 0:
                eta = (time.time() - t0) / i * (len(todo) - i)
                status = "done=%d/%d found=%d none=%d eta=%.0fmin" % (
                    i, len(todo), found, none_count, eta / 60)
                with open(PROGRESS, "w", encoding="utf-8") as pf:
                    pf.write(status + "\n")
                print(status)

    with open(PROGRESS, "w", encoding="utf-8") as pf:
        pf.write("COMPLETE done=%d found=%d none=%d\n" % (len(todo), found, none_count))
    print("COMPLETE done=%d found=%d none=%d" % (len(todo), found, none_count))


if __name__ == "__main__":
    main()