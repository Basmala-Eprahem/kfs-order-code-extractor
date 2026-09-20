"""Batch image processing for the OCR web app.

Flow per job:  validate/keep original files -> run the existing OCR pipeline
(extract_value) on a decoded copy -> rename each image by the extracted
6-digit code (duplicate-safe) -> failed images go to failed/ -> results.csv
-> one ZIP with the renamed images + failed/ + results.csv.
"""
import csv
import logging
import os
import re
import shutil
import threading
import uuid
import zipfile

import cv2
import numpy as np

import config
from app.services.extractor import extract_value

log = logging.getLogger(__name__)

CODE_RE = re.compile(r"^\d{6}$")

# In-memory job registry:  job_id -> job dict (guarded by JOBS_LOCK).
JOBS = {}
JOBS_LOCK = threading.Lock()

DETECT_TO_EXT = {
    "jpg": ".jpg", "jpeg": ".jpeg", "png": ".png", "webp": ".webp",
    "bmp": ".bmp", "tiff": ".tiff", "gif": ".gif", "heic": ".heic",
    "heif": ".heif",
}


def _safe_name(name):
    """Filesystem-safe basename of a user filename."""
    base = os.path.basename(name or "")
    base = re.sub(r"[^\w.\- ]", "_", base).strip()
    return base or "image"


# ---------------------------------------------------------------------------
# Image type detection / decoding
# ---------------------------------------------------------------------------
def detect_format(path):
    """Return a content-based image type ('jpg', 'png', ...) or None."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(32)
    except OSError:
        return None

    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head[:2] == b"BM":
        return "bmp"
    if head[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand in (b"heic", b"heix", b"hevc", b"hevs"):
            return "heic"
        if brand in (b"mif1", b"msf1", b"heif", b"heim"):
            return "heif"
    return None


def decode_bgr(path):
    """Decode any supported image file into a BGR numpy array (or None)."""
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is not None:
        return img
    try:
        from PIL import Image
        with Image.open(path) as im:
            if im.mode != "RGB":
                im = im.convert("RGB")
            rgb = np.asarray(im)
    except Exception as exc:  # UnidentifiedImageError, OSError, ...
        log.debug("Pillow fallback failed for %s: %s", path, exc)
        return None
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def process_one(path):
    """Run the EXISTING OCR pipeline on one file.

    Returns (code_or_None, error_message_or_None). The code must be exactly
    6 digits to be considered a valid document number.
    """
    try:
        img = decode_bgr(path)
        if img is None:
            return None, "Unsupported or corrupted image"
        result = extract_value(img)
        value = result.get("value")
        if value and CODE_RE.match(value):
            return value, None
        return None, "No valid 6-digit code found"
    except Exception as exc:
        log.exception("process_one %s failed", path)
        return None, "OCR error: %s" % exc


# ---------------------------------------------------------------------------
# Naming helpers (duplicate-safe)
# ---------------------------------------------------------------------------
def _final_ext(original_name, detected):
    """Prefer the original extension; fall back to the detected type."""
    ext = os.path.splitext(original_name)[1].lower()
    if ext in config.ALLOWED_EXTENSIONS:
        return ext
    return DETECT_TO_EXT.get(detected, "")


def _unique_filename(used, stem, ext):
    """Return stem[_{n}]ext, registering it in 'used'."""
    n = used.get(stem, 0)
    used[stem] = n + 1
    return (stem if n == 0 else "%s_%d" % (stem, n)) + ext


# ---------------------------------------------------------------------------
# CSV / ZIP
# ---------------------------------------------------------------------------
CSV_COLUMNS = ["original_filename", "final_filename", "extracted_code",
               "status", "error_message"]


def write_results_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in CSV_COLUMNS})


def build_zip(zip_dest, rows, csv_path):
    """One ZIP: renamed successes at root, failed/ subfolder, results.csv."""
    with zipfile.ZipFile(zip_dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for row in rows:
            src, final = row["_src"], row["final_filename"]
            if not src or not final:
                continue
            arc = final if row["status"] == "success" else "failed/" + final
            zf.write(src, arc)
        zf.write(csv_path, "results.csv")


# ---------------------------------------------------------------------------
# Job lifecycle
# ---------------------------------------------------------------------------
def new_job():
    """Register an empty job (files are saved by the caller afterwards)."""
    job_id = uuid.uuid4().hex
    job = {
        "id": job_id,
        "status": "running",
        "message": "",
        "total": 0,
        "current": 0,
        "success": 0,
        "failed": 0,
        "rows": [],
        "root": os.path.join(config.JOB_DIR, job_id),
        "zip_path": None,
        "csv_path": None,
    }
    with JOBS_LOCK:
        JOBS[job_id] = job
    os.makedirs(job["root"], exist_ok=True)
    return job_id


def start_job(job_id, entries):
    """Set the job's files and launch the background worker."""
    job = get_job(job_id)
    if job is None:
        return
    job["total"] = len(entries)
    t = threading.Thread(target=_run_batch, args=(job_id, list(entries)),
                         daemon=True)
    t.start()


def get_job(job_id):
    with JOBS_LOCK:
        return JOBS.get(job_id)


def _run_batch(job_id, entries):
    job = get_job(job_id)
    ok_dir = os.path.join(job["root"], "ok")
    fail_dir = os.path.join(job["root"], "failed")
    os.makedirs(ok_dir, exist_ok=True)
    os.makedirs(fail_dir, exist_ok=True)

    ok_used = {}
    fail_used = {}
    rows = []
    try:
        for original_name, path in entries:
            try:
                code, err = process_one(path)
            except Exception as exc:  # last-resort per-file guard
                log.exception("batch item %s", original_name)
                code, err = None, "Processing error: %s" % exc

            if code:
                detected = detect_format(path)
                final = _unique_filename(ok_used, code,
                                         _final_ext(original_name, detected) or "")
                dest = os.path.join(ok_dir, final)
                try:
                    shutil.move(path, dest)
                except OSError:
                    shutil.copyfile(path, dest)
                    try:
                        os.remove(path)
                    except OSError:
                        pass
                rows.append({
                    "original_filename": original_name,
                    "final_filename": final,
                    "extracted_code": code,
                    "status": "success",
                    "error_message": "",
                    "_src": dest,
                })
                job["success"] += 1
            else:
                final = _safe_name(original_name)
                stem, ext = os.path.splitext(final)
                final = _unique_filename(fail_used, stem or "image", ext)
                dest = os.path.join(fail_dir, final)
                try:
                    shutil.move(path, dest)
                except OSError:
                    shutil.copyfile(path, dest)
                    try:
                        os.remove(path)
                    except OSError:
                        pass
                rows.append({
                    "original_filename": original_name,
                    "final_filename": final,
                    "extracted_code": "",
                    "status": "failed",
                    "error_message": err or "failed",
                    "_src": dest,
                })
                job["failed"] += 1

            job["current"] += 1

        # CSV + ZIP
        os.makedirs(config.BATCH_DIR, exist_ok=True)
        csv_path = os.path.join(job["root"], "results.csv")
        write_results_csv(csv_path, rows)
        zip_path = os.path.join(config.BATCH_DIR, "%s.zip" % job_id)
        build_zip(zip_path, rows, csv_path)
        job["csv_path"] = os.path.join(config.BATCH_DIR, "%s.csv" % job_id)
        shutil.copyfile(csv_path, job["csv_path"])
        job["zip_path"] = zip_path

        job["rows"] = [_without_src(r) for r in rows]
        job["status"] = "done"
    except Exception as exc:
        log.exception("batch %s crashed", job_id)
        job["status"] = "error"
        job["message"] = str(exc)
    finally:
        shutil.rmtree(job["root"], ignore_errors=True)


def _without_src(row):
    return {k: v for k, v in row.items() if k != "_src"}