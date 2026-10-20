"""确保手机版 HTTP 服务只公开网页文件和玩家选择的合并音效。"""

import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from mobile import AUDIO_FILE, WEB_ROOT, create_server


class MobileServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = create_server("127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_serves_mobile_page_and_modules(self) -> None:
        for path, expected_type in (
            ("/", "text/html"),
            ("/app.mjs", "text/javascript"),
            ("/game.mjs", "text/javascript"),
            ("/style.css", "text/css"),
            ("/manifest.webmanifest", "application/manifest+json"),
        ):
            with self.subTest(path=path), urlopen(self.base_url + path) as response:
                self.assertEqual(response.status, 200)
                self.assertTrue(response.headers.get_content_type().startswith(expected_type))

    def test_serves_only_the_selected_merge_sound(self) -> None:
        with urlopen(self.base_url + "/audio_review/win_A.wav") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers.get_content_type(), "audio/wav")
            self.assertEqual(response.read(), AUDIO_FILE.read_bytes())

    def test_does_not_expose_project_files_or_directory_listings(self) -> None:
        self.assertTrue((WEB_ROOT.parent / "2048_save.json").exists())
        for path in ("/2048_save.json", "/game.py", "/tests/", "/web/"):
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                urlopen(self.base_url + path)
            self.assertEqual(error.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
