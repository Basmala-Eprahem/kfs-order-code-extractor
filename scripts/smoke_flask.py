import sys, os, io
from io import BytesIO
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app

app = create_app()
client = app.test_client()

r = client.get("/")
body = r.get_data(as_text=True)
assert "ارفع صورة" in body and r.status_code == 200
assert "folder" not in body.lower(), "folder picker should be gone"

with open(r"C:\Users\M lapan\Desktop\ocr\images\1 (10).jpg", "rb") as fh:
    r = client.post("/extract", data={"image": (fh, "1 (10).jpg")},
                    content_type="multipart/form-data")
body = r.get_data(as_text=True)
assert "329955" in body, "value missing"
assert "أرقام طويلة" not in body
print("upload extraction OK")

with open(r"C:\Users\M lapan\Desktop\ocr\images\1 (105).jpg", "rb") as fh:
    r = client.post("/extract", data={"image": (fh, "1 (105).jpg")},
                    content_type="multipart/form-data")
assert "لم يتم العثور" in r.get_data(as_text=True)
print("unreadable -> clear message OK")

r = client.post("/extract", data={"image": (BytesIO(b"%PDF-1.4"), "x.pdf")},
                content_type="multipart/form-data")
assert "خطأ" in r.get_data(as_text=True)
print("bad extension rejected OK")
print("ALL OK")