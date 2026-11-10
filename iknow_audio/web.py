"""Local demo: upload an environmental sound and inspect CLAP plus AKG."""

import json
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from experiment import ROOT, predict


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return
        body = (ROOT / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/predict":
            self.send_error(404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 20_000_000:
                raise ValueError("Audio phải có dung lượng từ 1 byte đến 20 MB.")
            suffix = self.headers.get("X-Audio-Extension", "").lower()
            if suffix not in {".wav", ".flac", ".mp3", ".ogg"}:
                raise ValueError("Chỉ nhận WAV, FLAC, MP3 hoặc OGG.")
            with tempfile.NamedTemporaryFile(suffix=suffix, dir=ROOT / "data", delete=False) as file:
                file.write(self.rfile.read(size))
                path = Path(file.name)
            try:
                result = predict(path)
                result.pop("audio", None)
            finally:
                path.unlink(missing_ok=True)
            status = 200
        except Exception as exc:
            status = 400
            result = {"error": str(exc)}
        body = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    host, port = "127.0.0.1", 8766
    print(f"http://{host}:{port}", flush=True)
    HTTPServer((host, port), Handler).serve_forever()
