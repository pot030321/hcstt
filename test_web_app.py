"""Small end-to-end check of the local browser API, including real audio input."""

import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

from app import Handler


class WebAppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_page_text_and_audio(self):
        with urlopen(self.url + "/?demo=1") as response:
            self.assertIn("Tải audio", response.read().decode("utf-8"))
        with urlopen(self.url + "/api/kb?disease=Acute%20laryngitis") as response:
            kb = json.load(response)
        self.assertEqual(49, kb["counts"]["disease"])
        self.assertEqual(605, kb["counts"]["has_symptom"])
        self.assertTrue(any(row["code"] == "E_91" and row["relation"] == "has_symptom" for row in kb["relations"]))
        request = Request(self.url + "/api/analyze", json.dumps({"text": "I have a fever and a cough"}).encode(), {"Content-Type": "application/json"}, method="POST")
        with urlopen(request) as response:
            data = json.load(response)
        self.assertEqual({"E_91", "E_201"}, {item["code"] for item in data["matched"]})
        self.assertEqual(24, data["candidate_count"])
        self.assertEqual(11, data["top_ties"])
        sample = Path(__file__).parent / "samples" / "influenza_demo.mp3"
        with urlopen(self.url + "/samples/influenza_demo.mp3") as response:
            self.assertEqual("audio/mpeg", response.headers["Content-Type"])
            self.assertEqual(sample.read_bytes(), response.read())
        request = Request(self.url + "/api/transcribe", sample.read_bytes(), {"X-Audio-Extension": ".mp3"}, method="POST")
        with urlopen(request) as response:
            transcript = json.load(response)["transcript"]
        self.assertIn("runny nose", transcript.lower())
        self.assertIn("chills", transcript.lower())
        self.assertIn("sore throat", transcript.lower())
        request = Request(self.url + "/api/analyze", json.dumps({"text": transcript}).encode(), {"Content-Type": "application/json"}, method="POST")
        with urlopen(request) as response:
            result = json.load(response)
        self.assertEqual({"E_181", "E_94", "E_97"}, {item["code"] for item in result["matched"]})
        self.assertEqual("Influenza", result["diseases"][0]["name"])
        self.assertEqual(1, result["top_ties"])


if __name__ == "__main__":
    unittest.main()
