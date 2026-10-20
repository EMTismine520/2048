"""下载已核实 CC0 授权的候选音效，生成独立于游戏的试听材料。"""

from __future__ import annotations

import hashlib
import html
import json
import wave
from base64 import b64decode
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
REVISION = "4596a49eaf5a533948d49a47467f606bcdea70ff"
BASE = "https://api.github.com/repos/Calinou/kenney-interface-sounds/contents"
SOURCE = "https://kenney.nl/assets/interface-sounds"
ORIGINAL_RELEASE = "https://opengameart.org/content/interface-sounds"
CANDIDATES = [
    ("move", "移动", "A", "click_002.wav"),
    ("move", "移动", "B", "click_001.wav"),
    ("merge", "合并", "A", "pluck_001.wav"),
    ("merge", "合并", "B", "glass_001.wav"),
    ("undo", "撤销", "A", "back_001.wav"),
    ("undo", "撤销", "B", "back_003.wav"),
    ("win", "胜利", "A", "confirmation_001.wav"),
    ("win", "胜利", "B", "confirmation_002.wav"),
    ("game_over", "结束", "A", "error_004.wav"),
    ("game_over", "结束", "B", "error_005.wav"),
]


def download(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "2048-audio-review"})
    with urlopen(request, timeout=30) as response:
        document = json.load(response)
    if document.get("encoding") != "base64":
        raise ValueError("下载内容不是预期的文件响应")
    return b64decode(document["content"])


def create_mix(records: list[dict], variant: str) -> None:
    selected = [record for record in records if record["variant"] == variant]
    channels, width, rate = 2, 2, 44100
    silence_byte = b"\x80" if width == 1 else b"\0"
    gap = silence_byte * round(rate * 0.7) * channels * width
    repeat_gap = silence_byte * round(rate * 0.3) * channels * width
    position = 0.0
    with wave.open(str(ROOT / f"set_{variant}.wav"), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(width)
        output.setframerate(rate)
        for index, record in enumerate(selected):
            with wave.open(str(ROOT / record["file"]), "rb") as source:
                actual = (source.getnchannels(), source.getsampwidth(), source.getframerate())
                if actual not in ((1, width, rate), (channels, width, rate)):
                    raise ValueError(f"不兼容的 WAV 参数：{record['file']}")
                frames = source.readframes(source.getnframes())
                if source.getnchannels() == 1:
                    frames = b"".join(frames[index:index + width] * 2 for index in range(0, len(frames), width))
            record["mix_start_seconds"] = round(position, 3)
            output.writeframes(frames)
            output.writeframes(repeat_gap)
            output.writeframes(frames)
            position += 2 * record["duration_seconds"] + 0.3
            if index + 1 < len(selected):
                output.writeframes(gap)
                position += 0.7


def build_page(records: list[dict]) -> str:
    rows = []
    for index in range(0, len(records), 2):
        pair = records[index:index + 2]
        cells = []
        for record in pair:
            filename = html.escape(record["file"])
            original = html.escape(record["original_filename"])
            choice = f"{record['label']}{record['variant']}"
            cells.append(
                f'<td><label><input type="radio" name="{record["event"]}" '
                f'value="{record["variant"]}"> {choice}</label>'
                f'<audio controls preload="none" src="{filename}" aria-label="{choice}试听"></audio>'
                f'<small>{original} · {record["duration_seconds"]:.3f} 秒</small></td>'
            )
        rows.append(f'<tr><th scope="row">{pair[0]["label"]}</th>{"".join(cells)}</tr>')
    template = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>2048 音效试听审批</title>
<style>
body{font:16px/1.6 system-ui,"Microsoft YaHei",sans-serif;background:#faf8ef;color:#443e38;margin:0}
main{max-width:880px;margin:auto;padding:28px 20px}h1{font-size:26px;margin:0 0 10px}
p{margin:8px 0 20px}table{width:100%;border-collapse:collapse}th,td{padding:14px 10px;text-align:left;border-bottom:1px solid #d8cfc5}
audio{display:block;width:100%;max-width:310px;margin:8px 0}label{font-weight:600}small{display:block;color:#665d54}
.sets{display:flex;gap:28px;flex-wrap:wrap}.sets>section{flex:1;min-width:240px}
button{font:inherit;padding:8px 14px;cursor:pointer}textarea{display:block;box-sizing:border-box;width:100%;padding:12px;margin-top:12px;font:inherit}
footer{margin-top:24px;font-size:14px}a{color:#73502e}
@media(max-width:540px){main{padding:20px 12px}td,th{padding:10px 4px}audio{min-width:100px}th{width:36px}small{overflow-wrap:anywhere}}
</style></head><body><main>
<h1>2048 音效试听审批</h1>
<p>五类操作各有 A / B 两个候选。先试听整组，再逐项比较；选好后把审批文字发回聊天。</p>
<div class="sets">
<section><h2>A 组</h2><audio controls preload="none" src="set_A.wav" aria-label="A组完整试听"></audio></section>
<section><h2>B 组</h2><audio controls preload="none" src="set_B.wav" aria-label="B组完整试听"></audio></section>
</div>
<p>整组顺序：移动 → 合并 → 撤销 → 胜利 → 结束。每个音效重复两次，操作之间间隔 0.7 秒。</p>
<table><thead><tr><th>操作</th><th>A 候选</th><th>B 候选</th></tr></thead><tbody>__ROWS__</tbody></table>
<p><button type="button" id="all-a">全选 A</button> <button type="button" id="all-b">全选 B</button></p>
<label for="approval">审批文字</label><textarea id="approval" rows="2" readonly placeholder="选择候选后自动生成，可复制到聊天"></textarea>
<p id="selection-status" role="status">尚未选择</p>
<footer>作者：Kenney。许可证：CC0。仅准备试听，尚未替换游戏音效。<br>
<a href="https://kenney.nl/assets/interface-sounds" target="_blank" rel="noopener">作者主页</a> ·
<a href="https://opengameart.org/content/interface-sounds" target="_blank" rel="noopener">原始发布页</a> ·
<a href="LICENSE.txt">原始许可证</a> · <a href="manifest.json">文件来源与校验记录</a></footer>
</main><script>
const events = [['move','移动'],['merge','合并'],['undo','撤销'],['win','胜利'],['game_over','结束']];
function update(){const choices=events.map(([key,label])=>{const el=document.querySelector('input[name="'+key+'"]:checked');return el?label+el.value:null});document.getElementById('approval').value=choices.filter(Boolean).join('、');document.getElementById('selection-status').textContent=choices.every(Boolean)?'已选择全部操作；复制审批文字发回聊天。':'已选择 '+choices.filter(Boolean).length+' / 5 项';}
document.querySelectorAll('input[type=radio]').forEach(el=>el.addEventListener('change',update));
for (const variant of ['A','B']) document.getElementById('all-'+variant.toLowerCase()).addEventListener('click',()=>{document.querySelectorAll('input[value="'+variant+'"]').forEach(el=>{el.checked=true});update()});
document.querySelectorAll('audio').forEach(el=>el.addEventListener('play',()=>{document.querySelectorAll('audio').forEach(other=>{if(other!==el)other.pause()})}));
</script></body></html>'''
    return template.replace("__ROWS__", "".join(rows))


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    license_path = ROOT / "LICENSE.txt"
    license_bytes = license_path.read_bytes() if license_path.exists() else download(f"{BASE}/LICENSE.txt?ref={REVISION}")
    if b"Creative Commons Zero, CC0" not in license_bytes:
        raise ValueError("下载的许可证不符合预期")
    (ROOT / "LICENSE.txt").write_bytes(license_bytes)
    records = []
    for event, label, variant, original in CANDIDATES:
        url = f"{BASE}/addons/kenney_interface_sounds/{original}?ref={REVISION}"
        filename = f"{event}_{variant}.wav"
        destination = ROOT / filename
        data = destination.read_bytes() if destination.exists() else download(url)
        destination.write_bytes(data)
        with wave.open(str(destination), "rb") as source:
            duration = source.getnframes() / source.getframerate()
            record = {
                "event": event, "label": label, "variant": variant,
                "file": filename, "original_filename": original,
                "duration_seconds": duration, "sample_rate": source.getframerate(),
                "channels": source.getnchannels(), "sample_width": source.getsampwidth(),
                "sha256": hashlib.sha256(data).hexdigest(), "download_url": url,
                "author": "Kenney", "license": "CC0-1.0",
            }
        records.append(record)
    create_mix(records, "A")
    create_mix(records, "B")
    manifest = {
        "review_status": "pending_user_approval", "source": SOURCE,
        "original_release": ORIGINAL_RELEASE,
        "download_mirror_revision": REVISION,
        "processing": "Individual WAV files are unmodified. Mixes duplicate mono samples into stereo, without gain changes. Each clip repeats twice, with 0.3s within-pair and 0.7s between-role silence.",
        "candidates": records,
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "index.html").write_text(build_page(records), encoding="utf-8")
    print(json.dumps([{"id": item["event"] + "_" + item["variant"], "seconds": round(item["duration_seconds"], 3), "format": [item["sample_rate"], item["channels"], item["sample_width"]]} for item in records], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
