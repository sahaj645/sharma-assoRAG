# upload.py
import requests

url = "http://127.0.0.1:3000/extract-text"

pdf_files = [
    "BNS.pdf",
    "BSA.pdf",
    "BNSS.pdf"
]

for pdf_path in pdf_files:
    with open(pdf_path, "rb") as f:
        files = {"file": (pdf_path, f, "application/pdf")}
        response = requests.post(url, files=files)
        if response.status_code == 200:
            print(f"✅ Uploaded {pdf_path} successfully")
        else:
            print(f"❌ Failed to upload {pdf_path}: {response.text}")