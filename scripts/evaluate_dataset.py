"""Evaluate the extraction pipeline over the dataset.

Usage:
    python scripts/evaluate_dataset.py            # all images
    python scripts/evaluate_dataset.py 120        # first 120 images
    python scripts/evaluate_dataset.py --sample 80 80   # 80 images, step 80

Writes outputs/extraction_results.csv and outputs/evaluation_summary.txt.
"""
import argparse
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2

import config
from app.services.extractor import extract_value

ROWS = ["filename", "orientation", "label", "method", "value", "processing_ms"]


def safe_value(v):
    if v is None:
        return ""
    return ",".join(v) if isinstance(v, list) else str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("limit", nargs="?", type=int, default=0)
    ap.add_argument("--sample", nargs=2, type=int, default=(0, 0))
    args = ap.parse_args()

    files = sorted(os.listdir(config.DATASET_DIR))
    files = [f for f in files if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if args.sample[1]:
        _, step = args.sample
        files = files[::step][:args.sample[0]]
    elif args.limit:
        files = files[:args.limit]

    out_csv = os.path.join(config.OUTPUT_DIR, "extraction_results.csv")
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=ROWS)
        writer.writeheader()

        ok_label = ok_any = none = 0
        t0 = time.time()
        for i, name in enumerate(files, 1):
            img = cv2.imread(os.path.join(config.DATASET_DIR, name))
            if img is None:
                writer.writerow({"filename": name, "processing_ms": "corrupt"})
                continue
            s = time.time()
            r = extract_value(img)
            ms = int((time.time() - s) * 1000)
            writer.writerow({
                "filename": name,
                "orientation": r.get("orientation"),
                "label": safe_value(r.get("label")),
                "method": safe_value(r.get("method")),
                "value": safe_value(r.get("value")),
                "processing_ms": ms,
            })
            if r.get("value"):
                ok_any += 1
                if r.get("method") == "label":
                    ok_label += 1
            else:
                none += 1
            if i % 25 == 0:
                print(f"  ... {i}/{len(files)}")
        elapsed = time.time() - t0

    summary = os.path.join(config.OUTPUT_DIR, "evaluation_summary.txt")
    with open(summary, "w", encoding="utf-8") as fh:
        fh.write(f"Images processed : {len(files)}\n")
        fh.write(f"Value found      : {ok_any} ({100.0 * ok_any / max(1, len(files)):.1f}%)\n")
        fh.write(f"  via label      : {ok_label}\n")
        fh.write(f"No value found   : {none}\n")
        fh.write(f"Elapsed          : {elapsed:.1f}s ({(elapsed / max(1, len(files))):.2f}s/img)\n")

    print(f"\nProcessed {len(files)} images -> {out_csv}")
    print(f"Value found: {ok_any} ({100.0 * ok_any / max(1, len(files)):.1f}%), "
          f"via label: {ok_label}, none: {none}")
    print(f"Summary -> {summary}")


if __name__ == "__main__":
    main()