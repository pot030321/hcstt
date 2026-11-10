"""Local browser demo for English audio/text symptom lookup."""

import json
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from kb import load_kb, map_text, rank, transcribe
from kb_store import explain, summary


ROOT = Path(__file__).parent
EVIDENCES, CONDITIONS = load_kb()
ALLOWED_AUDIO = {".wav", ".mp3", ".flac", ".ogg"}


def analyze(text):
    text = text.strip()
    if not text or len(text) > 2000:
        raise ValueError("Hãy nhập mô tả triệu chứng tiếng Anh (tối đa 2.000 ký tự).")
    matched, ignored = map_text(text, EVIDENCES)
    codes = {code for _, code, _ in matched}
    results = rank(CONDITIONS, codes) if len(codes) >= 2 else []
    ties = sum(abs(score - results[0][0]) < 1e-9 for score, _, _ in results) if results else 0
    return {
        "matched": [
            {"clause": clause, "code": code, "similarity": score, "question": EVIDENCES[code]["question_en"]}
            for clause, code, score in matched
        ],
        "ignored": ignored,
        "distinct_symptoms": len(codes),
        "candidate_count": len(results),
        "top_ties": ties,
        "diseases": [
            {"name": name, "score": round(score, 3), "links": [
                {"code": code, "question": EVIDENCES[code]["question_en"]} for code in links
            ]}
            for score, name, links in results[:5]
        ],
    }


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        request = urlsplit(self.path)
        if request.path == "/samples/influenza_demo.mp3":
            data = (ROOT / "samples" / "influenza_demo.mp3").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if request.path == "/api/kb":
            from urllib.parse import parse_qs

            name = parse_qs(request.query).get("disease", ["Acute laryngitis"])[0]
            if name not in CONDITIONS:
                self.reply(404, {"error": "Bệnh không có trong cơ sở tri thức."})
                return
            self.reply(200, {**summary(), "selected": name, "relations": explain(name)})
            return
        if request.path != "/":
            self.send_error(404)
            return
        data = (ROOT / "web" / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path not in ("/api/analyze", "/api/transcribe"):
            self.send_error(404)
            return
        limit = 16_384 if self.path == "/api/analyze" else 10 * 1024 * 1024
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= limit:
                self.reply(413, {"error": "Dữ liệu gửi lên rỗng hoặc vượt giới hạn kích thước."})
                return
            body = self.rfile.read(length)
            if self.path == "/api/analyze":
                payload = json.loads(body)
                if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
                    raise ValueError("Dữ liệu văn bản không hợp lệ.")
                self.reply(200, analyze(payload["text"]))
                return
            suffix = "." + self.headers.get("X-Audio-Extension", "").lower().lstrip(".")
            if suffix not in ALLOWED_AUDIO:
                raise ValueError("Chỉ nhận file WAV, MP3, FLAC hoặc OGG.")
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as file:
                file.write(body)
                path = Path(file.name)
            try:
                transcript = transcribe(path)
            finally:
                path.unlink(missing_ok=True)
            self.reply(200, {"transcript": transcript})
        except (ValueError, OSError, RuntimeError, json.JSONDecodeError) as exc:
            self.reply(400, {"error": str(exc)})


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    url = "http://127.0.0.1:8765/"
    print(f"Open: {url}  (Ctrl+C to stop)", flush=True)
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
