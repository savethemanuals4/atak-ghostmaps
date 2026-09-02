#!/usr/bin/env python3
"""
Regenerate index.kml: an ATAK-ready KML of NetworkLinks pointing at the
newest KMZ in each S2Underground GhostMaps product folder.

Run manually:  python3 build_index.py            (uses the GitHub API)
               python3 build_index.py --local /path/to/GhostMaps-clone
Or let the GitHub Actions workflow in .github/workflows/update.yml run it.
"""
import json, os, re, sys, urllib.request
from datetime import datetime
from urllib.parse import quote
from xml.sax.saxutils import escape

OWNER, REPO, BRANCH = "s2underground", "GhostMaps", "main"
ROOT = "ArcGIS Data for ATAK (KMZs)"
RAW = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/"
REFRESH_SECONDS = 3600
# Optional: path to a local clone of GhostMaps (used by the workflow); else GitHub API
LOCAL = sys.argv[sys.argv.index("--local") + 1] if "--local" in sys.argv else None  # GitHub's raw CDN caches 5 min; hourly is plenty

# (folder shown in ATAK, link name, repo sub-folder, filename prefix filter)
# "latest" = newest date parsed from the filename inside that sub-folder.
PRODUCTS = [
    ("Common Intelligence Picture", "CIP Master Database (latest)",
     f"{ROOT}/Common Intelligence Picture/Master Database", "S2Underground_Common_Intelligence_Picture"),
    ("Common Intelligence Picture", "Kinetic Activities - Last 30 Days",
     f"{ROOT}/Common Intelligence Picture/30-Day Pulls", "Kinetic_Activities_Last_30_Days"),
    ("Border Crisis Map", "Border Crisis Map (latest)",
     f"{ROOT}/Border Crisis Map", "S2Underground_Border_Crisis_Map"),
    ("Border Crisis Map", "Europe Migration Crisis (latest)",
     f"{ROOT}/Border Crisis Map/European Layers Only", "Europe_Migration_Crisis"),
]

DATE_RE = re.compile(r"_([A-Z][a-z]+)_(\d{1,2})_(\d{4})_(?:Export_)?v?(\d+)")

def file_key(name):
    m = DATE_RE.search(name)
    if not m:
        return (datetime.min, 0)
    mon, day, year, rev = m.groups()
    try:
        return (datetime.strptime(f"{mon} {day} {year}", "%B %d %Y"), int(rev))
    except ValueError:
        return (datetime.min, 0)

def list_dir(path):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{quote(path)}?ref={BRANCH}"
    req = urllib.request.Request(url, headers={"User-Agent": "atak-index-builder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def latest_kmz(path, prefix):
    if LOCAL:  # walk a local clone of GhostMaps instead of calling the API
        d = os.path.join(LOCAL, path)
        files = [f"{path}/{n}" for n in os.listdir(d)
                 if os.path.isfile(os.path.join(d, n)) and n.startswith(prefix) and n.lower().endswith(".kmz")]
    else:
        files = [e["path"] for e in list_dir(path)
                 if e["type"] == "file" and e["name"].startswith(prefix) and e["name"].lower().endswith(".kmz")]
    if not files:
        sys.exit(f"no KMZ matching {prefix} in {path}")
    return max(files, key=lambda p: file_key(p.rsplit("/", 1)[-1]))

def main():
    folders = {}
    for folder, label, path, prefix in PRODUCTS:
        f = latest_kmz(path, prefix)
        folders.setdefault(folder, []).append((label, f))

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<kml xmlns="http://www.opengis.net/kml/2.2">',
           '  <Document>',
           '    <name>S2 GhostMaps (auto-updating)</name>',
           f'    <description>Generated {datetime.utcnow():%Y-%m-%d %H:%M} UTC. Links resolve to the newest export in each GhostMaps folder.</description>']
    for folder, links in folders.items():
        out.append(f'    <Folder>\n      <name>{escape(folder)}</name>')
        for label, path in links:
            href = RAW + quote(path)
            out += ['      <NetworkLink>',
                    f'        <name>{escape(label)}</name>',
                    f'        <description>{escape(path.rsplit("/",1)[-1])}</description>',
                    '        <Link>',
                    f'          <href>{escape(href)}</href>',
                    '          <refreshMode>onInterval</refreshMode>',
                    f'          <refreshInterval>{REFRESH_SECONDS}</refreshInterval>',
                    '        </Link>',
                    '      </NetworkLink>']
        out.append('    </Folder>')
    out += ['  </Document>', '</kml>', '']
    with open("index.kml", "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    for folder, links in folders.items():
        for label, path in links:
            print(f"{label:38} -> {path.rsplit('/',1)[-1]}")

if __name__ == "__main__":
    main()
