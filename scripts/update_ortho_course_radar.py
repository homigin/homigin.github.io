#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


ROOT = Path(__file__).resolve().parents[1] / "static" / "ortho-course-radar"
TODAY = date.today()
TIMEOUT = 6


@dataclass(frozen=True)
class Source:
    name: str
    cat: str
    urls: tuple[str, ...] = ()
    wp: str | None = None
    verify: bool = True


SOURCES = [
    Source("TOA 台灣骨科醫學會", "綜合", ("https://bone.org.tw/education/", "https://www.toaa.org.tw/news/all/1", "https://www.toaa.org.tw/products/all/1"), verify=False),
    Source("JRS 台灣關節重建醫學會", "關節重建", ("https://jrs.org.tw/events/",), wp="https://jrs.org.tw"),
    Source("台灣關節鏡及膝關節醫學會", "運動醫學", ("https://www.taiwanarthroscopy.org.tw/category/activity/",), wp="https://www.taiwanarthroscopy.org.tw"),
    Source("TOTA 台灣骨科創傷醫學會", "創傷", ("https://www.tota.org.tw/category/news/",), wp="https://www.tota.org.tw"),
    Source("TWSS 台灣脊椎外科醫學會", "脊椎", ("https://www.twss.org.tw/",)),
    Source("TORS 台灣骨科研究學會", "研究", ("https://www.tors.org.tw/",)),
    Source("TOFAS 台灣足踝醫學會", "足踝", ("https://www.tofas.org.tw/",)),
    Source("TSES 台灣肩肘醫學會", "肩肘", ("https://www.shoulder-elbow.org.tw/category/conference/",), wp="https://www.shoulder-elbow.org.tw", verify=False),
    Source("TSSH 台灣手外科醫學會", "手外科", ("https://handsurgery.com.tw/category/new/", "https://www.tssh.org.tw/")),
    Source("TASM 台灣運動醫學醫學會", "運動醫學", ("https://www.tasm.org.tw/", "https://www.tasm.org.tw/news/")),
    Source("TNMSKUS 台灣神經肌肉骨骼超音波醫學會", "超音波", ("https://www.tnmskus.org.tw/seminar/all/1",)),
    Source("台灣骨質疏鬆症學會", "骨鬆", ("https://www.toa1997.org.tw/",)),
    Source("台灣疼痛醫學會", "疼痛", ("https://pain.org.tw/index.php/news_page/news_page2_content", "https://pain.org.tw/")),
    Source("台灣介入性疼痛醫學會", "疼痛", ("https://rapm.org.tw/news", "https://rapm.org.tw/index")),
    Source("復健醫學會 MSK / sports / pain", "復健相關", ("https://www.pmr.org.tw/active_news/active.asp", "https://www.pmr.org.tw/hot/hot.asp")),
    Source("AO Trauma Taiwan", "創傷", ("https://www.aofoundation.org/trauma/education/courses",)),
    Source("AO Recon", "關節重建", ("https://www.aofoundation.org/recon/education/courses",)),
    Source("IRCAD Taiwan", "手術訓練", ("https://www.ircadtaiwan.com/",)),
    Source("Chang Gung STARC", "手術訓練", ("https://starc.cgmh.org.tw/",)),
]

UNKNOWN_SOURCES = [
    "各醫學中心骨科教育課程：多數已由 TOA 學術活動頁部分涵蓋",
    "Cadaver Lab / Simulation Center：多數已由 TOA 學術活動頁 keyword 部分涵蓋",
    "Resident Camp / Young Surgeon Forum / Fellowship announcement：需要指定可公開抓的入口頁",
]

KEEP = re.compile(
    r"骨科|關節|膝|髖|肩|肘|手|腕|足|踝|脊椎|脊柱|創傷|骨折|骨鬆|骨質疏鬆|"
    r"運動醫學|關節鏡|超音波|疼痛|神經阻斷|cadaver|simulation|resident|"
    r"young surgeon|fellowship|workshop|course|camp|forum|meeting|congress|"
    r"TKA|THA|ACL|MSK|POCUS|arthroplasty|arthroscopy|spine|trauma",
    re.I,
)
DROP = re.compile(r"登入|隱私|privacy|cookie|聯絡|contact|關於|理監事|章程|會員|下載專區|facebook|line|通過名單|下載證書|宣導影片|^read more$|^continue reading$", re.I)
DATE_PATTERNS = [
    re.compile(r"(20\d{2})[./\-年](\d{1,2})[./\-月](\d{1,2})"),
    re.compile(r"(1\d{2})[./\-年](\d{1,2})[./\-月](\d{1,2})"),
]


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


def first_date(text: str, fallback: str | None = None) -> str | None:
    for pat in DATE_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        y, mo, d = map(int, m.groups())
        if y < 1911:
            y += 1911
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            pass
    return fallback


def category(source_cat: str, text: str) -> str:
    tests = [
        ("運動醫學", r"sports|ACL|arthroscop|關節鏡|運動醫學"),
        ("關節重建", r"TKA|THA|arthroplasty|關節重建|人工關節|髖關節|膝關節"),
        ("創傷", r"trauma|fracture|創傷|骨折"),
        ("脊椎", r"spine|脊椎|脊柱"),
        ("手外科", r"hand|wrist|手外科|腕"),
        ("足踝", r"foot|ankle|足踝"),
        ("肩肘", r"shoulder|elbow|肩|肘"),
        ("超音波", r"ultrasound|MSK|POCUS|超音波"),
        ("疼痛", r"pain|疼痛|神經阻斷|介入"),
        ("骨鬆", r"osteoporosis|骨鬆|骨質疏鬆"),
        ("研究", r"research|研究|論文|registry"),
    ]
    return next((name for name, pat in tests if re.search(pat, text, re.I)), source_cat)


def fetch(url: str, verify: bool = True) -> str:
    headers = {"User-Agent": "ortho-course-radar/0.1 (+local personal use)"}
    r = requests.get(url, headers=headers, timeout=TIMEOUT, verify=verify)
    r.raise_for_status()
    if not r.encoding or "charset=" not in r.headers.get("content-type", "").lower():
        r.encoding = r.apparent_encoding
    return r.text


def from_html(source: Source) -> list[dict[str, str]]:
    out = []
    last_error: Exception | None = None
    fetched = False
    for page in source.urls:
        try:
            soup = BeautifulSoup(fetch(page, source.verify), "html.parser")
            fetched = True
        except Exception as exc:
            last_error = exc
            continue
        for tr in soup.find_all("tr"):
            cells = [clean(td.get_text(" ")) for td in tr.find_all("td")]
            if len(cells) < 2:
                continue
            text = " ".join(cells)
            if DROP.search(text) or not KEEP.search(text):
                continue
            event_date = first_date(text)
            a = tr.find("a", href=True)
            if not event_date or not a:
                continue
            out.append({
                "date": event_date,
                "title": cells[1][:140],
                "source": source.name,
                "cat": category(source.cat, text),
                "place": cells[4] if len(cells) > 4 else "原公告",
                "url": urljoin(page, a["href"]),
            })
        for a in soup.find_all("a", href=True):
            title = re.sub(r"^(閱讀全文|Read more|Continue Reading)\s*", "", clean(a.get_text(" ")), flags=re.I)
            href = urljoin(page, a["href"])
            context = clean(a.parent.get_text(" ") if a.parent else title)
            text = f"{title} {context}"
            if not title or len(title) < 4 or DROP.search(text) or not KEEP.search(text):
                continue
            event_date = first_date(text)
            if not event_date:
                continue
            out.append({
                "date": event_date,
                "title": title[:140],
                "source": source.name,
                "cat": category(source.cat, text),
                "place": "原公告",
                "url": href,
            })
    if not fetched and last_error:
        raise last_error
    return out


def from_wp(source: Source) -> list[dict[str, str]]:
    assert source.wp
    api = f"{source.wp.rstrip('/')}/wp-json/wp/v2/posts?per_page=50&_fields=link,title,excerpt,content,date"
    posts: list[dict[str, Any]] = requests.get(api, timeout=TIMEOUT, verify=source.verify).json()
    out = []
    for post in posts:
        title = clean(post.get("title", {}).get("rendered", ""))
        body = BeautifulSoup(str(post.get("excerpt", {}).get("rendered", "")) + str(post.get("content", {}).get("rendered", "")), "html.parser").get_text(" ")
        text = clean(f"{title} {body}")
        if not title or DROP.search(text) or not KEEP.search(text):
            continue
        published = str(post.get("date", ""))[:10] or None
        event_date = first_date(text, published)
        if not event_date:
            continue
        out.append({
            "date": event_date,
            "title": title[:140],
            "source": source.name,
            "cat": category(source.cat, text),
            "place": "原公告",
            "url": post.get("link", source.wp),
        })
    return out


def keep_recent(event: dict[str, str]) -> bool:
    try:
        d = date.fromisoformat(event["date"])
    except ValueError:
        return False
    return d >= TODAY - timedelta(days=30)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    events: list[dict[str, str]] = []
    errors: dict[str, str] = {}
    for source in SOURCES:
        try:
            if source.wp:
                events.extend(from_wp(source))
            if source.urls:
                events.extend(from_html(source))
        except Exception as exc:
            errors[source.name] = f"{type(exc).__name__}: {exc}"

    seen = set()
    deduped = []
    for event in sorted(filter(keep_recent, events), key=lambda e: (e["date"], e["source"], e["title"])):
        key = event["url"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)

    (ROOT / "events.js").write_text(
        "window.ORTHO_EVENTS = " + json.dumps(deduped, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    (ROOT / "last-run.json").write_text(
        json.dumps({
            "updated": datetime.now().isoformat(timespec="seconds"),
            "events": len(deduped),
            "errors": errors,
            "not_configured_yet": UNKNOWN_SOURCES,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(deduped)} events; {len(errors)} source errors")

    # ponytail: catches bad source edits without a test framework.
    assert all(e["date"] and e["title"] and e["url"].startswith(("http://", "https://")) for e in deduped)


if __name__ == "__main__":
    main()
