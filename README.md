# ATAK link to S2Underground GhostMaps

`index.kml` is a KML of NetworkLinks that always point at the newest KMZ in each
[GhostMaps](https://github.com/s2underground/GhostMaps) product folder.
`build_index.py` regenerates it; the GitHub Actions workflow runs that every 6 hours
and commits the result, so ATAK only ever needs one URL.

## Setup (once)
1. In the repo: Settings → Actions → General → Workflow permissions → **Read and write**.
2. Actions tab → "Refresh GhostMaps index" → Run workflow (first run confirms it works).
3. In ATAK: Import Manager → **Import from URL** (or Overlay Manager → Remote Resources)
   and paste
   `https://raw.githubusercontent.com/savethemanuals4/atak-ghostmaps/main/index.kml`

ATAK re-fetches each NetworkLink hourly; the index itself is re-resolved every 6 hours,
so a new S2U export appears on your map without touching the app.

Excluded on purpose: `BaseData/Demographics/USA_Census_Ethnicity_Data_2020.kmz`
(564 MB uncompressed — too large for a mobile device).

Data licence: S2 Underground, CC BY-NC-SA 4.0.
