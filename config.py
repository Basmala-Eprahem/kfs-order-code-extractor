"""Application configuration.

All important settings live here so they are not hardcoded inside
pipeline modules or routes.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATASET_DIR = os.path.join(BASE_DIR, "images")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
SAMPLES_DIR = os.path.join(OUTPUT_DIR, "samples")
BATCH_DIR = os.path.join(OUTPUT_DIR, "batches")   # finished batch ZIPs live here
JOB_DIR = os.path.join(UPLOAD_DIR, "batch")         # temp per-job working folders

# ---------------------------------------------------------------------------
# Uploads / Security
# ---------------------------------------------------------------------------
# Extensions accepted by the upload system. The actual image type is ALSO
# validated from the file content (magic bytes), never from the filename
# extension alone. Users may upload real documents in any of these formats.
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp",
                      ".tif", ".tiff", ".gif", ".heic", ".heif"}
# Large batch uploads (1000s of files) share one request body.
MAX_CONTENT_LENGTH = 4 * 1024 * 1024 * 1024  # 4 GB

# ---------------------------------------------------------------------------
# Tesseract
# ---------------------------------------------------------------------------
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
OCR_LANGS = "ara+eng"
OCR_NUMERIC_LANG = "eng"          # numeric-only config (ASCII digits)
OCR_NUMERIC_WHITELIST = "0123456789"

# ---------------------------------------------------------------------------
# Target field
# ---------------------------------------------------------------------------
TARGET_FIELD_NAME = "كود الطلب"

# Expected characteristics of the value found during dataset analysis.
# Visible 'كود الطلب' labels pair with long 015-prefixed numbers, e.g.
# 015080022037437 (15-16 digits). Extraction first uses the label, then
# falls back to this pattern.
EXPECTED_NUMBER_LENGTH = 15
EXPECTED_NUMBER_PATTERN = r"015\d{12}"
FALLBACK_CODE_PATTERN = r"015\s?\d{10,}"

# ---------------------------------------------------------------------------
# Orientation handling
# ---------------------------------------------------------------------------
ORIENTATION_CANDIDATES = (0, 90, 180, 270)
ORIENTATION_CONFIDENCE_THRESHOLD = 0.55

# ---------------------------------------------------------------------------
# Processing limits (protects against adversarial/large images)
# ---------------------------------------------------------------------------
MAX_IMAGE_SIDE = 4000
PROCESS_SIDE = 2200  # downscale long side to this for analysis/OCR

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
DEBUG = os.environ.get("OCR_DEBUG", "0") == "1"
SECRET_KEY = os.environ.get("OCR_SECRET_KEY", "dev-insecure-secret-change-me")