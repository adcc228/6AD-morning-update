"""Build feed.xml (Apple Podcasts / Spotify compatible) and index.html from episodes/*/.
Each episode folder: episode.mp3 + meta.json {"title","summary","date":"YYYY-MM-DD"}.
Keeps the newest MAX_EPISODES folders; older ones are deleted to keep the repo small.
"""
import json, os, glob, shutil, subprocess, html
from datetime import datetime, timezone
from email.utils import format_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "config.json")))
BASE = CFG["base_url"].rstrip("/")
MAX_EPISODES = CFG.get("max_episodes", 30)

def duration(mp3):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3],
                         capture_output=True, text=True).stdout.strip()
    s = int(float(out or 0)); return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"

eps = sorted(glob.glob(os.path.join(HERE, "episodes", "*", "meta.json")), reverse=True)
for old in eps[MAX_EPISODES:]:
    shutil.rmtree(os.path.dirname(old))
eps = eps[:MAX_EPISODES]

items, rows = [], []
for m in eps:
    d = os.path.dirname(m); slug = os.path.basename(d)
    meta = json.load(open(m)); mp3 = os.path.join(d, "episode.mp3")
    if not os.path.exists(mp3): continue
    url = f"{BASE}/episodes/{slug}/episode.mp3"
    pub = datetime.fromisoformat(meta["date"]).replace(hour=6, minute=30, tzinfo=timezone.utc)
    t, s = html.escape(meta["title"]), html.escape(meta["summary"])
    items.append(f"""    <item>
      <title>{t}</title>
      <description>{s}</description>
      <itunes:summary>{s}</itunes:summary>
      <enclosure url="{url}" length="{os.path.getsize(mp3)}" type="audio/mpeg"/>
      <guid isPermaLink="false">morning-update-{slug}</guid>
      <pubDate>{format_datetime(pub)}</pubDate>
      <itunes:duration>{duration(mp3)}</itunes:duration>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:explicit>false</itunes:explicit>
    </item>""")
    rows.append(f'<li><strong>{t}</strong><br><audio controls preload="none" src="episodes/{slug}/episode.mp3"></audio>'
                f'<br><a href="episodes/{slug}/script.txt">Transcript</a></li>')

owner = CFG.get("owner_email", "")
owner_xml = f"<itunes:owner><itunes:name>{html.escape(CFG['author'])}</itunes:name><itunes:email>{owner}</itunes:email></itunes:owner>" if owner else ""
block = "<itunes:block>Yes</itunes:block>" if CFG.get("private", True) else ""
feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{html.escape(CFG['title'])}</title>
    <link>{BASE}/</link>
    <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>
    <language>en-gb</language>
    <description>{html.escape(CFG['description'])}</description>
    <itunes:summary>{html.escape(CFG['description'])}</itunes:summary>
    <itunes:author>{html.escape(CFG['author'])}</itunes:author>
    {owner_xml}
    <itunes:image href="{BASE}/cover.jpg"/>
    <image><url>{BASE}/cover.jpg</url><title>{html.escape(CFG['title'])}</title><link>{BASE}/</link></image>
    <itunes:category text="Business"><itunes:category text="Investing"/></itunes:category>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    {block}
    <lastBuildDate>{format_datetime(datetime.now(timezone.utc))}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""
open(os.path.join(HERE, "feed.xml"), "w").write(feed)
open(os.path.join(HERE, "index.html"), "w").write(f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(CFG['title'])}</title>
<style>body{{font-family:-apple-system,Segoe UI,sans-serif;max-width:680px;margin:2rem auto;padding:0 16px;background:#0f1f2e;color:#f4efe6}}
a{{color:#c9a45c}}li{{margin:1.2rem 0;list-style:none}}audio{{width:100%;margin-top:.4rem}}code{{background:#1c3044;padding:2px 6px;border-radius:4px}}</style>
<img src="cover.jpg" width="160" alt=""><h1>{html.escape(CFG['title'])}</h1><p>{html.escape(CFG['description'])}</p>
<p>Apple Podcasts: Library → ••• → Follow a Show by URL → <code>{BASE}/feed.xml</code></p><ul>{''.join(rows)}</ul>
""")
print(f"feed.xml built with {len(items)} episodes")
