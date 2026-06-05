# BK (Bill Kang) — Lyrics Corpus Reference

> Artist: BK (@bkofficialmusic) | 台灣 Lo-fi R&B | Spotify 月聽眾 256,826  
> 藝術家本名：康洺勳 | YouTube: @bkofficialmusic (70.7K)  
> NetEase artist ID: **52652468**  
> GitHub repo: https://github.com/meowju/lofi-rnb-lyrics-skills

## Corpus Summary (2026-06-05)

| Metric | Value |
|--------|-------|
| Hot songs (NetEase) | 50 |
| Songs with lyrics | 44 |
| Missing songs | 6 |
| Collection rate | 88% |

## Collected Songs (44)

### Hot (with play counts)
| Song | NetEase ID | Source | Plays |
|------|-----------|--------|-------|
| 你知道你比晚霞好看嗎 | 2702706805 | YouTube VTT + NetEase | 10.4M |
| 第一次見妳的我 | 2086104586 | NetEase | 3.1M |
| 凌晨三點 | 2026519908 | NetEase | 2.9M |
| 凌晨三點 2025 | 2735860634 | NetEase | — |
| 凌晨三點 pt2 | 2600827511 | NetEase | — |
| 給妳的愛 | 2667981036 | YouTube VTT + NetEase pt.2 | 2.8M |
| 給妳的愛 pt.2 | 2667981036 | NetEase (full) | — |
| 還是會想念 | 3386263291 | NetEase | — |
| 妳對我多重要 | 2042294200 | NetEase | 2.2M |
| 寂寞的夜 | YT-YcxBYUDYaQI | YouTube VTT | — |

### Other collected (31 more)
See `lyrics/bk-lyrics-raw.md` in the repo for full text.

## Missing Songs (6)
These returned NO_LYRICS from NetEase and no useful YouTube subtitles:
- 就算了吧 (2086091183)
- 我們都沒有錯 (3381472485)
- 寫給祢的信 (3373420070)
- 妳不是妳，我不是我 (2097237306)
- 給妳的愛 (2042303582) — use pt.2 instead
- Toxic (DJ Sliqe/BK) (435409879) — English song
- Truthfully2025 (2725604434) — partial only (English-dominant)

## Key Lyric Phrases (frequency analysis)

Top 5-char phrases across 44-song corpus:
- 最美的 ___ — 14 occurrences
- 但妳卻走遠 — 12
- 關於妳 ___ — 12
- 再煩我了 — 12
- 現在是凌晨三點 — 10

Top English words:
- Oh — 80x
- Baby / Girl — 47x each
- Yeah — 37x
- Uh / Ah — 21x / 40x
- I / You / My — 30+ each

## Similar Artists to Collect Next
| Artist | NetEase search term | Expected songs |
|--------|---------------------|----------------|
| Juice Boy | Juice Boy 台灣 | ~20 |
| PPlin | PPlin 台灣 | ~15 |
| Vigoz | Vigoz 台灣 | ~20 |
| 8lak | 8lak 台灣 | ~15 |
| Aioz | Aioz 台灣 | ~10 |
| 尹熙龙 YIN. | 尹熙龙 台灣 | ~15 |

## Prompt Templates for Style Analysis

To extract style patterns from a new artist corpus:

```python
# 1. Phrase frequency
from collections import Counter
import re
all_lines = []
for s in songs_with_lyrics:
    all_lines.extend([l.strip() for l in s['lyrics'].split('\n') if l.strip()])

phrase_counter = Counter()
for line in all_lines:
    for i in range(len(line) - 3):
        phrase = line[i:i+5]
        if len(phrase) == 5 and not re.search(r'[a-zA-Z0-9]', phrase):
            phrase_counter[phrase] += 1
for phrase, count in phrase_counter.most_common(30):
    if count >= 2:
        print(f"  {phrase}: {count}")

# 2. English word frequency
english_words = Counter()
for line in all_lines:
    words = re.findall(r'[A-Za-z]+', line)
    for w in words:
        english_words[w.lower()] += 1
for w, c in english_words.most_common(20):
    if c >= 2:
        print(f"  {w}: {c}")
```

## GitHub Push Template

```python
import time, jwt, json, urllib.request, subprocess

APP_ID = "3737759"
INSTALLATION_ID = "136247983"  # meowju org
PRIVATE_KEY_PATH = "/opt/data/github-app.pem"

with open(PRIVATE_KEY_PATH) as f:
    private_key_pem = f.read()

now = int(time.time())
jwt_token = jwt.encode(
    {"iat": now, "exp": now + 600, "iss": APP_ID},
    private_key_pem, algorithm="RS256"
)

req = urllib.request.Request(
    f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens",
    method="POST",
    headers={
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    },
    data=b"{}"
)
with urllib.request.urlopen(req, timeout=30) as resp:
    gh_token = json.loads(resp.read())["token"]

subprocess.run(["git", "add", "-A"], cwd=repo_path)
subprocess.run(["git", "commit", "-m", "feat: add lyrics corpus"], cwd=repo_path)
subprocess.run(
    ["git", "push", f"https://x-access-token:{gh_token}@github.com/meowju/{repo}.git", "main"],
    cwd=repo_path, capture_output=True, timeout=30
)
```

## Collection Log
- 2026-06-05: Initial collection — 44/50 songs, pushed to `meowju/lofi-rnb-lyrics-skills`
