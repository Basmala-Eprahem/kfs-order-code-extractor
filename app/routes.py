import os
import uuid

import cv2
from flask import (Blueprint, current_app, jsonify, render_template, request,
                   send_file, send_from_directory, url_for)

import config
from app.services import batch
from app.services.extractor import extract_value, _rot

bp = Blueprint("app", __name__)


def _allowed(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in config.ALLOWED_EXTENSIONS


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/extract", methods=["POST"])
def extract():
    file = request.files.get("image")
    if file is None or file.filename == "":
        return _render_result("error", message="اختر ملف صورة أولًا.")
    if not _allowed(file.filename):
        return _render_result("error", message="امتداد غير مسموح.")

    upload_name = f"{uuid.uuid4().hex}_{batch._safe_name(file.filename)}"
    path = os.path.join(current_app.config["UPLOAD_DIR"], upload_name)
    file.save(path)
    img = batch.decode_bgr(path)
    try:
        os.remove(path)
    except OSError:
        pass
    if img is None:
        return _render_result("error", message="تعذر فتح الصورة (ملف تالف أو صيغة غير مدعومة).")
    return _render_output(img, file.filename)


def _render_output(img, filename):
    h, w = img.shape[:2]
    side = max(h, w)
    if side > config.MAX_IMAGE_SIDE:
        sc = config.MAX_IMAGE_SIDE / side
        img = cv2.resize(img, (int(w * sc), int(h * sc)))

    result = extract_value(img)

    preview_name = None
    if result.get("orientation"):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        preview = _rot(gray, result["orientation"])
        preview_name = f"{uuid.uuid4().hex}.jpg"
        cv2.imwrite(os.path.join(current_app.config["PREVIEW_DIR"], preview_name), preview)

    return _render_result("result",
                          value=result.get("value"),
                          label=result.get("label"),
                          method=result.get("method"),
                          orientation=result.get("orientation"),
                          preview=preview_name,
                          filename=filename)


@bp.route("/preview/<name>")
def preview(name):
    safe = os.path.basename(name)
    return send_from_directory(current_app.config["PREVIEW_DIR"], safe)


@bp.route("/batch/start", methods=["POST"])
def batch_start():
    files = request.files.getlist("images")
    files = [f for f in files if f and f.filename]
    if not files:
        return jsonify({"error": "لم يتم اختيار أي صور."}), 400
    if len(files) > 5000:
        return jsonify({"error": "أقصى عدد للصور في الدفعة الواحدة هو 5000."}), 400

    job_id = batch.new_job()
    root = os.path.join(config.JOB_DIR, job_id)
    os.makedirs(root, exist_ok=True)

    stored = []
    for f in files:
        name = batch._safe_name(f.filename)
        path = os.path.join(root, f"{uuid.uuid4().hex}__{name}")
        f.save(path)
        stored.append((name, path))

    batch.start_job(job_id, stored)
    return jsonify({"job_id": job_id})


@bp.route("/batch/<job_id>/progress")
def batch_progress(job_id):
    job = batch.get_job(job_id)
    if job is None:
        return jsonify({"status": "missing"}), 404
    payload = {
        "job_id": job_id,
        "status": job["status"],
        "message": job.get("message", ""),
        "current": job["current"],
        "total": job["total"],
        "success": job["success"],
        "failed": job["failed"],
    }
    if job["status"] == "done":
        payload["zip_url"] = url_for("app.batch_download", job_id=job_id)
        payload["rows"] = job.get("rows", [])
    return jsonify(payload)


@bp.route("/batch/<job_id>/download")
def batch_download(job_id):
    job = batch.get_job(job_id)
    if job is None or not job.get("zip_path") or not os.path.exists(job["zip_path"]):
        return jsonify({"error": "الملف غير متاح أو انتهت صلاحيته."}), 404
    return send_file(job["zip_path"], as_attachment=True,
                     download_name=f"processed_images_{job_id[:8]}.zip")


def _render_result(kind, **kw):
    return render_template("result.html", kind=kind, **kw)