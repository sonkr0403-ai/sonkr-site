"""블로그·유튜브 최신 글을 읽어 data/feed.json 으로 저장합니다.

GitHub Actions 가 하루 한 번 실행합니다. 사이트(index.html)는 이 파일을 읽어
'블로그 새 글'과 '유튜브 최신 영상' 칸을 채웁니다.
"""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

BLOG_ID = "sonkr0403"
BLOG_RSS = f"https://rss.blog.naver.com/{BLOG_ID}.xml"
YT_CHANNEL = "UCmFRSGDD6Zu0FYCai-mvd8w"
YT_RSS = f"https://www.youtube.com/feeds/videos.xml?channel_id={YT_CHANNEL}"

# 사이트 후기 칸에 고정으로 올려 둔 글. '블로그 새 글'에서는 빼서 두 번 보이지 않게 합니다.
FIXED_REVIEWS = {"224389454887", "224361997406", "224353480946", "224338290903"}

BLOG_COUNT = 4
YT_COUNT = 3
OUT = Path(__file__).resolve().parent.parent / "data" / "feed.json"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (sonkr-site feed bot)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def blog_items():
    root = ET.fromstring(get(BLOG_RSS))
    items = []
    for it in root.iter("item"):
        link = (it.findtext("link") or "").strip()
        m = re.search(r"/(\d{9,})", link)
        if not m or m.group(1) in FIXED_REVIEWS:
            continue
        log_no = m.group(1)
        try:
            date = parsedate_to_datetime(it.findtext("pubDate") or "").strftime("%Y.%m.%d")
        except (TypeError, ValueError):
            date = ""
        items.append({
            "title": (it.findtext("title") or "").strip(),
            "url": f"https://blog.naver.com/{BLOG_ID}/{log_no}",
            "date": date,
            "category": (it.findtext("category") or "").strip(),
        })
        if len(items) >= BLOG_COUNT:
            break
    return items


def youtube_items():
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    root = ET.fromstring(get(YT_RSS))
    items = []
    for e in root.findall("a:entry", ns):
        vid = e.findtext("yt:videoId", default="", namespaces=ns)
        link = e.find("a:link", ns)
        href = link.get("href", "") if link is not None else ""
        if not vid or "/shorts/" in href:  # 쇼츠는 빼고 일반 영상만
            continue
        published = e.findtext("a:published", default="", namespaces=ns)
        items.append({
            "id": vid,
            "title": e.findtext("a:title", default="", namespaces=ns).strip(),
            "date": published[:10].replace("-", "."),
        })
        if len(items) >= YT_COUNT:
            break
    return items


def main():
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    data = {"blog": old.get("blog", []), "youtube": old.get("youtube", [])}
    # 한쪽을 못 읽어도 다른 쪽은 갱신하고, 못 읽은 쪽은 이전 내용을 유지합니다.
    for key, fn in (("blog", blog_items), ("youtube", youtube_items)):
        try:
            got = fn()
            if got:
                data[key] = got
            print(f"{key}: {len(got)}개")
        except Exception as exc:  # noqa: BLE001
            print(f"{key}: 읽기 실패 - {exc}")
    if not data["blog"] and not data["youtube"]:
        print("가져온 내용 없음")
        return
    if data.get("blog") == old.get("blog") and data.get("youtube") == old.get("youtube"):
        print("변경 없음")
        return
    data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("feed.json 갱신")


if __name__ == "__main__":
    main()
