#!/usr/bin/env python3
"""CI 定时抓取地缘要闻 → data/news.json
在 GitHub Actions 里跑，访客只读静态 JSON：无第三方代理、无 IP 泄露、不受代理停服影响。"""
import json, re, sys, urllib.request, xml.etree.ElementTree as ET, datetime as dt, pathlib

FEEDS = [
    ("德国之声中文", "https://rss.dw.com/xml/rss-chi-all"),
    ("RFI法广中文", "https://www.rfi.fr/cn/rss"),
    ("纽约时报中文网", "https://cn.nytimes.com/rss"),
]
KW = re.compile("战争|冲突|停火|停战|制裁|关税|军事|军演|军费|导弹|无人机|袭击|空袭|加沙|乌克兰|俄罗斯|伊朗|以色列|叙利亚|也门|胡塞|台海|南海|朝鲜|稀土|锂|镍|钴|铜|矿产|石油|天然气|原油|OPEC|军售|军贸|国防|核|制裁|禁运|出口管制|供应链|航道|红海|苏伊士|霍尔木兹|北约|欧盟|美联储|美债|去美元|黄金|白银|通胀|大选|政变|停摆")

def clean(t):
    t = re.sub(r"<[^>]+>", "", t or "")
    return re.sub(r"\s+", " ", t).strip()

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (news-bot)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def parse(xml_bytes, name):
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []
    out = []
    for item in root.iter("item"):
        g = lambda tag: (item.findtext(tag) or "").strip()
        title = clean(g("title"))
        if not title:
            continue
        out.append({
            "title": title,
            "link": g("link"),
            "desc": clean(g("description"))[:140],
            "date": g("pubDate"),
            "src": name,
        })
    return out

def main():
    items, failures = [], []
    for name, url in FEEDS:
        try:
            items += parse(fetch(url), name)
        except Exception as e:
            failures.append(f"{name}: {e}")
    # 宁缺毋滥：只保留命中地缘关键词的条目
    hits = [it for it in items if KW.search(it["title"] + " " + it["desc"])]
    seen, uniq = set(), []
    for it in hits:
        k = re.sub(r"\s+", "", it["title"])[:42]
        if k in seen:
            continue
        seen.add(k)
        uniq.append(it)
    out = {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "snapshot_date": "2026-09-24",
        "source": "GitHub Actions 定时抓取（三源 RSS，关键词过滤）",
        "raw_count": len(items),
        "hit_count": len(uniq),
        "failures": failures,
        "items": uniq[:40],
    }
    path = pathlib.Path("data/news.json")
    # 守卫：抓取失败/命中为 0 时【不覆盖】已有快照 —— 否则一次网络抖动就清空数据
    if not uniq:
        print(f"⚠ 本次命中 0 条（原始 {len(items)} 条，失败源 {len(failures)}）→ 保留原 {path} 不动")
        return 1
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✅ 抓取 {len(items)} 条 → 命中 {len(uniq)} 条 ｜ 失败源 {len(failures)} → 已写入 {path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
