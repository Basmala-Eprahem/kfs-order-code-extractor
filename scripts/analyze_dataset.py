"""Dataset analysis and report generation.

Scans the dataset directory, computes per-image statistics, detects
orientation variations, corrupt images, and produces:

    outputs/dataset_report.csv
    outputs/samples/contact_sheet_*.jpg   (representative samples)

Usage:
    python scripts/analyze_dataset.py
"""
import argparse
import csv
import glob
import os
import sys

import cv2
import numpy as np

# Allow running from project root or from anywhere.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

SUPPORTED = {".jpg", ".jpeg", ".png"}


def load_image(path):
    """Read a 3-channel image; returns (bgr, ok)."""
    img = cv2.imread(path)
    if img is None:
        return None, False
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img, True


def dominant_orientation_sharp(image):
    """Estimate base orientation using rotated tile contrast vs rotation.

    Compute the fraction of dark pixels in each rotation using an adaptive
    threshold: a normal upright document usually results in more foreground
    matter for the correct rotation. Pure heuristic — the final decision is
    made by the OCR pipeline via the target keyphrase.
    """
    small = cv2.resize(image, (400, 400))
    scores = {}
    for angle, rot in (
        (0, small),
        (90, cv2.rotate(small, cv2.ROTATE_90_CLOCKWISE)),
        (180, cv2.rotate(small, cv2.ROTATE_180)),
        (270, cv2.rotate(small, cv2.ROTATE_90_COUNTERCLOCKWISE)),
    ):
        g = cv2.cvtColor(rot, cv2.COLOR_BGR2GRAY)
        thr = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 41, 15)
        scores[angle] = float(np.mean(thr) / 255.0)
    return scores


def normalize_angle(angle):
    return angle % 360


def report_dataset(dataset_dir, sample_count):
    records = []
    corrupt = []

    files = []
    for ext in SUPPORTED:
        files += glob.glob(os.path.join(dataset_dir, "**", f"*{ext}"), recursive=True)
        files += glob.glob(os.path.join(dataset_dir, "**", f"*{ext.upper()}"), recursive=True)
    files = sorted(set(files))

    prev_shape = None
    prev_orient = None

    for f in files:
        try:
            img, ok = load_image(f)
        except Exception as exc:  # noqa: BLE001
            corrupt.append((f, f"read error: {exc}"))
            continue
        if not ok:
            corrupt.append((f, "corrupt/unreadable"))
            continue

        h, w = img.shape[:2]
        if prev_shape is None:
            prev_shape = (h, w)
        same_template = (h, w) == prev_shape

        # Only estimate orientation for a small sample of images to keep the
        # analysis phase reasonably fast.
        est_orient = 0
        if prev_orient is None and len(records) < 60:
            s = dominant_orientation_sharp(img)
            est_orient = normalize_angle(max(s, key=s.get))
        if prev_orient is None:
            prev_orient = est_orient
        same_orient = est_orient == prev_orient

        fsize = os.path.getsize(f)
        records.append({
            "filename": os.path.basename(f),
            "relative_path": os.path.relpath(f, dataset_dir),
            "extension": os.path.splitext(f)[1].lower(),
            "width": w,
            "height": h,
            "file_size_bytes": fsize,
            "aspect_ratio": round(w / h, 4) if h else None,
            "orientation": "portrait" if h >= w else "landscape",
            "est_rotation": est_orient,
            "same_template_size": same_template,
        })
        prev_shape = (h, w)
        prev_orient = est_orient

    return records, corrupt, files


def build_summary(records, corrupt, count):
    w = [r["width"] for r in records]
    h = [r["height"] for r in records]
    fs = [r["file_size_bytes"] for r in records]
    aspect = [r["aspect_ratio"] for r in records if r["aspect_ratio"]]
    portrait = sum(1 for r in records if r["orientation"] == "portrait")
    landscape = sum(1 for r in records if r["orientation"] == "landscape")
    exts = {}
    for r in records:
        exts[r["extension"]] = exts.get(r["extension"], 0) + 1
    sizes = {}
    for r in records:
        sizes[(r["width"], r["height"])] = sizes.get((r["width"], r["height"]), 0) + 1
    orients = {}
    for r in records:
        orients[r["est_rotation"]] = orients.get(r["est_rotation"], 0) + 1

    return {
        "total_images": count,
        "valid_images": len(records),
        "corrupt_images": len(corrupt),
        "extension_counts": exts,
        "width_min": min(w) if w else None,
        "width_max": max(w) if w else None,
        "width_avg": round(sum(w) / len(w), 1) if w else None,
        "height_min": min(h) if h else None,
        "height_max": max(h) if h else None,
        "height_avg": round(sum(h) / len(h), 1) if h else None,
        "aspect_min": min(aspect) if aspect else None,
        "aspect_max": max(aspect) if aspect else None,
        "portrait": portrait,
        "landscape": landscape,
        "size_bytes_min": min(fs) if fs else None,
        "size_bytes_max": max(fs) if fs else None,
        "size_bytes_avg": round(sum(fs) / len(fs), 1) if fs else None,
        "unique_dimensions": sizes,
        "est_rotations": orients,
        "template_size_consistent": len({(r["width"], r["height"]) for r in records}) == 1,
    }


def print_summary(s):
    print("=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)
    print(f"Total files found      : {s['total_images']}")
    print(f"Valid images           : {s['valid_images']}")
    print(f"Corrupt/unreadable     : {s['corrupt_images']}")
    print(f"Extensions             : {s['extension_counts']}")
    print(f"Width  min/max/avg     : {s['width_min']}/{s['width_max']}/{s['width_avg']}")
    print(f"Height min/max/avg     : {s['height_min']}/{s['height_max']}/{s['height_avg']}")
    print(f"Aspect ratio min/max   : {s['aspect_min']}/{s['aspect_max']}")
    print(f"Portrait / Landscape   : {s['portrait']} / {s['landscape']}")
    print(f"File size min/max/avg  : {s['size_bytes_min']}/{s['size_bytes_max']}/{s['size_bytes_avg']}")
    print(f"Unique dimensions      : {len(s['unique_dimensions'])}")
    for dim, n in sorted(s["unique_dimensions"].items(), key=lambda kv: -kv[1])[:10]:
        print(f"    {dim} -> {n}")
    print(f"Est. base rotations    : {s['est_rotations']}")
    print(f"Template size consistent: {s['template_size_consistent']}")


def write_csv(records, corrupt, csv_path):
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as fh:
        cols = [
            "filename", "relative_path", "extension", "width", "height",
            "file_size_bytes", "aspect_ratio", "orientation",
            "est_rotation", "same_template_size",
        ]
        wr = csv.DictWriter(fh, fieldnames=cols)
        wr.writeheader()
        for r in records:
            wr.writerow(r)
        for f, err in corrupt:
            wr.writerow({
                "filename": os.path.basename(f),
                "relative_path": f,
                "extension": os.path.splitext(f)[1].lower(),
                "width": "", "height": "", "file_size_bytes": "", "aspect_ratio": "",
                "orientation": "CORRUPT", "est_rotation": "", "same_template_size": "corrupt: " + err,
            })


def build_contact_sheet(files, count, out_path, cols=4):
    """Make a grid contact sheet with filename labels."""
    th = 220
    chosen = files[:count]
    sheets = []
    for i in range(0, len(chosen), cols * 4):
        batch = chosen[i:i + cols * 4]
        if not batch:
            break
        thumbs = []
        for f in batch:
            img, ok = load_image(f)
            if not ok:
                thumbs.append(np.full((th, th, 3), 32, dtype=np.uint8))
                continue
            h, w = img.shape[:2]
            scale = th / max(h, w)
            img = cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))))
            canvas = np.full((th, th, 3), 32, dtype=np.uint8)
            oh, ow = img.shape[:2]
            canvas[:oh, :ow] = img
            cv2.putText(canvas, os.path.basename(f)[:18], (4, th - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            thumbs.append(canvas)
        n = len(thumbs)
        while len(thumbs) < cols * 4:
            thumbs.append(np.full((th, th, 3), 32, dtype=np.uint8))
        rows = [np.hstack(thumbs[r * cols:(r + 1) * cols]) for r in range(4)]
        sheet = np.vstack(rows)
        sheets.append(sheet)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    for idx, sheet in enumerate(sheets):
        p = out_path if idx == 0 else out_path.replace(".jpg", f"_{idx + 1:02d}.jpg")
        cv2.imwrite(p, sheet)
        print(f"Contact sheet written: {p}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=config.DATASET_DIR)
    ap.add_argument("--output-dir", default=config.OUTPUT_DIR)
    ap.add_argument("--samples", type=int, default=16,
                    help="how many images to use for the contact sheet")
    args = ap.parse_args()

    records, corrupt, files = report_dataset(args.dataset, args.samples)
    summary = build_summary(records, corrupt, len(files))
    print_summary(summary)

    os.makedirs(args.output_dir, exist_ok=True)
    csv_path = os.path.join(args.output_dir, "dataset_report.csv")
    write_csv(records, corrupt, csv_path)
    print(f"\nReport written: {csv_path}")

    always_same = set(summary["unique_dimensions"].keys())
    if len(always_same) > 1:
        print(f"\nWARNING: {len(always_same)} different template sizes detected!")

    samples_dir = os.path.join(args.output_dir, "samples")
    os.makedirs(samples_dir, exist_ok=True)
    build_contact_sheet(files, args.samples, os.path.join(samples_dir, "contact_sheet.jpg"))

    print("\nDataset analysis complete.\n")
    print("IMPORTANT PENDING QUESTIONS (to answer in Phase 2):")
    print("  * Is the template consistent? (see unique_dimensions)")
    print("  * Where is 'كود الطلب' located in the layout?")
    print("  * What is the format/length of its value?")


if __name__ == "__main__":
    main()