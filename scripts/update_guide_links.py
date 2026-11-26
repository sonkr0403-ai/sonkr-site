"""학습 가이드 페이지마다 '다른 학습 가이드' 칸을 채웁니다.

guide/index.html 의 카드 목록을 읽어, 각 가이드 페이지의
<!-- guides:start --> ~ <!-- guides:end --> 사이를 다시 씁니다.
새 가이드를 추가한 뒤 한 번 실행하세요:  python3 scripts/update_guide_links.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARD = re.compile(r'<a class="gcard" href="(/guide/([^/"]+)/)"><span class="chip">([^<]*)</span><b>([^<]*)</b>')
START, END = "<!-- guides:start -->", "<!-- guides:end -->"


def main():
    cards = CARD.findall((ROOT / "guide" / "index.html").read_text(encoding="utf-8"))
    for _, slug, _, _ in cards:
        page = ROOT / "guide" / slug / "index.html"
        if not page.exists():
            continue
        others = [c for c in cards if c[1] != slug][:4]
        if not others:
            continue
        links = "\n".join(
            f'    <a href="{href}"><small>{chip}</small>{title}</a>' for href, _, chip, title in others
        )
        block = (f'{START}\n  <h2 style="font-size:24px;margin:44px 0 0">다른 학습 가이드</h2>\n'
                 f'  <div class="more">\n{links}\n  </div>\n  {END}')
        html = page.read_text(encoding="utf-8")
        if START in html:
            html = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, html, flags=re.S)
        else:
            html = html.replace('</main>', '  ' + block + '\n</main>', 1)
        page.write_text(html, encoding="utf-8")
        print("updated", slug)


if __name__ == "__main__":
    main()
