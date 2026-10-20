"""启动手机浏览器版：python mobile.py。只提供 web 目录中的静态文件。"""

from __future__ import annotations

import argparse
import socket
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parent / "web"
AUDIO_FILE = Path(__file__).resolve().parent / "audio_review" / "win_A.wav"


class MobileHandler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".mjs": "text/javascript"}

    def list_directory(self, path):
        self.send_error(404)
        return None

    def translate_path(self, path):
        resolved = Path(super().translate_path(path)).resolve()
        if not resolved.is_relative_to(WEB_ROOT):
            return str(WEB_ROOT / "__not_found__")
        return str(resolved)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/audio_review/win_A.wav":
            if not AUDIO_FILE.is_file():
                self.send_error(404)
                return
            payload = AUDIO_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        super().do_GET()


def create_server(host: str = "0.0.0.0", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), partial(MobileHandler, directory=str(WEB_ROOT)))


def main() -> None:
    parser = argparse.ArgumentParser(description="2048 手机浏览器版（同一 Wi-Fi 下访问）")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    try:
        server = create_server(args.host, args.port)
    except OSError as error:
        parser.exit(1, f"启动失败：{error}\n可尝试 python mobile.py --port 8001\n")
    port = server.server_port
    print(f"电脑预览：http://127.0.0.1:{port}", flush=True)
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)})
    except OSError:
        addresses = []
    for address in addresses:
        if not address.startswith("127."):
            print(f"手机访问：http://{address}:{port}", flush=True)
    print("手机和电脑需连接同一 Wi-Fi；关闭终端或按 Ctrl+C 停止。", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
