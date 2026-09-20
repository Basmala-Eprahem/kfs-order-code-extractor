"""End-to-end tests for the multi-image batch OCR flow.

Covers: multiple formats, distinct codes, duplicate codes, corrupted files,
no-code images, ZIP contents and CSV correctness, plus the existing
single-image mode.

Run:  python scripts/test_batch.py
"""
import io
import os
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
from io import BytesIO

from PIL import Image

from app import create_app

IMG = r"C:\Users\M lapan\Desktop\ocr\images"
TMP = r"C:\Users\M lapan\Desktop\ocr\outputs\test_assets"

KNOWN = {"1 (6).jpg": "329918", "1 (38).jpg": "331450", "1 (10).jpg": "329955"}

PASS = 0
FAIL = 0


def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  [OK] %s" % label)
    else:
        FAIL += 1
        print("  [FAIL] %s" % label)


def build_assets():
    os.makedirs(TMP, exist_ok=True)
    a = os.path.join(TMP, "a.png")
    b = os.path.join(TMP, "b.webp")
    c = os.path.join(TMP, "c.bmp")
    d = os.path.join(TMP, "d.gif")
    e = os.path.join(TMP, "e.tiff")
    nb = os.path.join(TMP, "no_code.jpg")
    img6 = cv2.imread(os.path.join(IMG, "1 (6).jpg"))
    img38 = cv2.imread(os.path.join(IMG, "1 (38).jpg"))
    img10 = cv2.imread(os.path.join(IMG, "1 (10).jpg"))
    cv2.imwrite(a, img6)
    cv2.imwrite(b, img38, [cv2.IMWRITE_WEBP_QUALITY, 90])
    cv2.imwrite(c, img10)
    with Image.open(os.path.join(IMG, "1 (6).jpg")) as im:
        im.convert("RGB").save(d, "GIF")
        im.convert("RGB").save(e, "TIFF")
    Image.new("RGB", (800, 600), (220, 220, 220)).save(nb, "JPEG")
    return a, b, c, d, e, nb


def multipart_files(file_list):
    """Build multipart form-data bytes with many files under one field."""
    import uuid
    boundary = uuid.uuid4().hex
    body = io.BytesIO()
    for name, stream in file_list:
        stream.seek(0)
        content = stream.read()
        body.write(b"--%b\r\n" % boundary.encode("ascii"))
        body.write(b'Content-Disposition: form-data; name="images"; filename="%b"\r\n'
                   % name.encode("utf-8"))
        body.write(b"Content-Type: application/octet-stream\r\n\r\n")
        body.write(content)
        body.write(b"\r\n")
    body.write(b"--%b--\r\n" % boundary.encode("ascii"))
    return body.getvalue(), boundary


def post_batch(client, file_list):
    data, boundary = multipart_files(file_list)
    return client.post("/batch/start", data=data,
                       content_type="multipart/form-data; boundary=%s" % boundary,
                       buffered=True)


def wait_job(client, job_id, timeout=300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = client.get("/batch/%s/progress" % job_id)
        p = r.get_json()
        if p["status"] in ("done", "error"):
            return p
        time.sleep(1.0)
    return {"status": "timeout"}


def main():
    assets = build_assets()
    a, b, c, d, e, nb = assets
    app = create_app()
    client = app.test_client()

    print("== TEST: single-image mode still works ==")
    with open(os.path.join(IMG, "1 (6).jpg"), "rb") as fh:
        r = client.post("/extract", data={"image": (fh, "1 (6).jpg")},
                        content_type="multipart/form-data")
    check("single extract returns 6-digit code", "329918" in r.get_data(as_text=True))

    print("== TEST: structural fallback reads previously-unreadable scans ==")
    with open(os.path.join(IMG, "1 (105).jpg"), "rb") as fh105:
        r = post_batch(client, [("previously_none.jpg", fh105)])
    js105 = r.get_json()
    p105 = wait_job(client, js105["job_id"])
    check("1 (105) now extracts its 6-digit code",
          p105["status"] == "done" and p105["success"] == 1)
    rows105 = {r0["original_filename"]: r0 for r0 in p105["rows"]}
    check("1 (105) -> 332007 via structural fallback",
          rows105.get("previously_none.jpg", {}).get("extracted_code") == "332007")

    print("== TEST: multiple formats + distinct codes ==")
    with open(nb, "rb") as fnb, \
         open(a, "rb") as fa, open(b, "rb") as fb, open(c, "rb") as fc, \
         open(d, "rb") as fd, open(e, "rb") as fe:
        files = [
            ("no_code.jpg", fnb),
            ("col1.png", fa),
            ("col2.webp", fb),
            ("col3.bmp", fc),
            ("col4.gif", fd),
            ("col5.tiff", fe),
            ("dup_same.jpg", fa),          # same bytes -> same code as col1
            ("broken.jpg", BytesIO(b"%PDF-1.4 not an image at all" * 4)),
        ]
        r = post_batch(client, files)
    js = r.get_json()
    check("batch start returns job id", "job_id" in js)
    job_id = js["job_id"]
    p = wait_job(client, job_id)
    check("batch completes", p["status"] == "done")
    print("  summary: total=%d success=%d failed=%d" %
          (p["total"], p["success"], p["failed"]))
    check("8 uploaded, 6 processed, 2 failed",
          p["total"] == 8 and p["success"] == 6 and p["failed"] == 2)

    rows = {r0["original_filename"]: r0 for r0 in p["rows"]}
    check("png -> 329918.png", rows.get("col1.png", {}).get("final_filename") == "329918.png")
    check("webp -> 331450.webp", rows.get("col2.webp", {}).get("final_filename") == "331450.webp")
    check("bmp  -> 329955.bmp", rows.get("col3.bmp", {}).get("final_filename") == "329955.bmp")
    check("gif  -> 329918_1.gif  (duplicate, ext preserved)",
          rows.get("col4.gif", {}).get("final_filename") == "329918_1.gif")
    check("tiff -> 329918_2.tiff (duplicate, ext preserved)",
          rows.get("col5.tiff", {}).get("final_filename") == "329918_2.tiff")
    check("no_code -> failed, original name kept",
          rows.get("no_code.jpg", {}).get("status") == "failed" and
          rows.get("no_code.jpg", {}).get("final_filename") == "no_code.jpg")
    check("corrupt -> failed with error",
          rows.get("broken.jpg", {}).get("status") == "failed" and
          bool(rows.get("broken.jpg", {}).get("error_message")))

    print("== TEST: ZIP contents ==")
    zr = client.get("/batch/%s/download" % job_id)
    check("zip downloadable", zr.status_code == 200)
    zf = zipfile.ZipFile(BytesIO(zr.data))
    names = set(zf.namelist())
    check("renamed images in zip root",
          {"329918.png", "331450.webp", "329955.bmp", "329918_1.gif",
           "329918_2.tiff", "329918_3.jpg"} <= names)
    check("failed preserved in failed/",
          names >= {"failed/no_code.jpg", "failed/broken.jpg"})
    check("results.csv present", "results.csv" in names)

    csv_data = zf.read("results.csv").decode("utf-8-sig")
    check("csv header correct",
          csv_data.splitlines()[0].startswith("original_filename,final_filename,extracted_code,status,error_message"))
    check("csv has 6 success + 2 failed",
          csv_data.count("success") == 6 and csv_data.count("failed") == 2)
    check("no image lost: 6 renamed + 2 failed + results.csv = 9 unique entries",
          len(names) == 9 and
          {"329918.png", "331450.webp", "329955.bmp", "329918_1.gif",
           "329918_2.tiff", "329918_3.jpg"} <
          {os.path.basename(n) for n in names})

    print("== TEST: larger batch (30 mixed files, incl. 24 corrupted) ==")
    files = []
    with open(os.path.join(IMG, "1 (6).jpg"), "rb") as fgood, \
         open(nb, "rb") as fnone:
        gd, nn = fgood.read(), fnone.read()
        for i in range(30):
            if i % 15 == 0:
                files.append(("big_%03d.jpg" % i, BytesIO(gd)))       # success
            elif i % 3 == 0:
                files.append(("big_%03d.gif" % i, BytesIO(nn)))       # failed (no code)
            else:
                files.append(("big_%03d.jpg" % i, BytesIO(b"garbage" * 8)))  # failed fast
    r = post_batch(client, files)
    j2 = r.get_json()
    p2 = wait_job(client, j2["job_id"], timeout=180)
    check("large batch completes", p2["status"] == "done")
    check("large batch: 2 success, 28 failed, none lost",
          p2["success"] == 2 and p2["failed"] == 28 and p2["total"] == 30)

    print("== TEST: 1000+ images in one batch (scale) ==")
    big_files = [("b_%04d.jpg" % i, BytesIO(b"corrupt-bytes" * 4)) for i in range(1000)]
    r = post_batch(client, big_files)
    p7 = wait_job(client, r.get_json()["job_id"], timeout=300)
    check("1000-image batch completes", p7["status"] == "done")
    check("1000 images processed, all failed, none lost",
          p7["total"] == 1000 and p7["failed"] == 1000 and p7["success"] == 0)
    zr = client.get("/batch/%s/download" % r.get_json()["job_id"])
    zf7 = zipfile.ZipFile(BytesIO(zr.data))
    names7 = zf7.namelist()
    check("zip has 1000 failed + results.csv",
          len(names7) == 1001 and names7.count("results.csv") == 1)

    print("\n%d passed, %d failed" % (PASS, FAIL))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()