# The Morning Update

A 20-minute, two-host weekday podcast covering markets, macro, regulation and fund news for a COO. It is written and voiced by Claude and published as a podcast RSS feed on GitHub Pages.

## Listen

- **Apple Podcasts (iPhone/Mac):** Library → ••• (top right) → **Follow a Show by URL** → paste `https://adcc228.github.io/6AD-morning-update/feed.xml`
- **Spotify:** Spotify can't follow a feed by URL. To get the show there, submit the feed once at creators.spotify.com (Add an existing show → RSS feed). Before you do, set `owner_email` in `config.json` (Spotify sends a verification code to it) and `"private": false`. Note that this makes the show publicly listed.
- **Browser:** `https://adcc228.github.io/6AD-morning-update/`

## Layout

- `episodes/YYYY-MM-DD/`: `script.txt` (transcript), `meta.json`, `episode.mp3`
- `tts.py`: offline text-to-speech (Kokoro British voices, espeak-ng phonemes). Usage: `python3 tts.py script.txt episode.mp3`
- `build_feed.py`: rebuilds `feed.xml` and `index.html` and keeps the latest 30 episodes
- `setup_assets.sh`: downloads the voice model (about 350 MB, not committed)

## Script format

Each line starts with `A:` (Emma) or `B:` (George). A line containing only `[PAUSE]` inserts a section break.
