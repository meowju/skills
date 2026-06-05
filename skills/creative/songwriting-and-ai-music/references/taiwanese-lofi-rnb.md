# Taiwanese Lo-fi R&B 曲風參考資料

> 基於 42 首真實歌詞（50首熱門曲）語料庫分析 | 更新：2026-06-05
> Live corpus: https://github.com/meowju/lofi-rnb-lyrics-skills

---

## 藝人檔案

### BK (Bill Kang) — 康洺勳
- **Spotify**: https://open.spotify.com/artist/6oUenG9cEPeZ4QYHXZGeFN | **月聽眾：256,826**
- **YouTube**: @bkofficialmusic | **70.7K subscribers**
- **StreetVoice**: https://streetvoice.com/bill7799/
- **所在地**: 台中市
- **製作人**: Vigoz（同時為藝人，最常合作）

**熱門曲 Spotify 播放量：**
| 歌曲 | 播放量 |
|------|--------|
| 你知道你比晚霞好看嗎 | 10.4M |
| 第一次見妳的我 | 3.1M |
| 凌晨三點 | 2.9M |
| 給妳的愛 | 2.8M |
| 妳對我多重要 | 2.2M |

---

## 歌詞收集方法（實測可行）

### 工具鏈

```bash
# 1. 找到藝人 NetEase ID（通过搜索）
curl -s -X POST "https://music.163.com/api/search/get" \
  -H "User-Agent: Mozilla/5.0" \
  -d "s=BK+台灣&type=100&limit=20&offset=0" | python3 -c "
import sys,json; d=json.load(sys.stdin)
for a in d['result']['artists'][:5]:
    if 'BK' in a['name']: print(a['id'], a['name'])
"

# 2. 批量抓熱門歌曲列表（50首）
curl -s "https://music.163.com/api/artist/{ARTIST_ID}" \
  -H "User-Agent: Mozilla/5.0" | python3 -c "
import sys,json; d=json.load(sys.stdin)
for s in d['hotSongs']:
    print(s['id'], s['name'])
"

# 3. 批量抓歌詞（LRC格式，無需登入）
curl -s "https://music.163.com/api/song/lyric?id={SONG_ID}&lv=1&kv=1&tv=-1" \
  -H "User-Agent: Mozilla/5.0" | python3 -c "
import sys,json,re; d=json.load(sys.stdin)
lrc = d['lrc']['lyric']
lines = re.sub(r'\[[\d:.]+\]', '', lrc).strip().split('\n')
for l in lines: l=l.strip()
"

# 4. YouTube 字幕（繞過JS驗證）
~/bin/yt-dlp --js-runtimes "node:$(which node)" \
  --write-auto-subs --sub-langs "zh-Hant,zh" \
  --skip-download --output "/tmp/bk_subs" "https://www.youtube.com/watch?v={VID}"
```

### 歌詞缺失時的備用策略
- YouTube lyric videos（搜尋「動態歌詞」+「BK」）
- MOJIM (mojim.com) — 台灣歌詞網
- StreetVoice — 有部分歌曲含歌詞

---

## 曲風特徵（基於語料庫統計）

### 高頻短語（5字）
| 短語 | 次數 | 含義 |
|------|------|------|
| 最美的 ___ | 14 | 讚美句式，妳就像最美的... |
| 但妳卻走遠 | 12 | 創傷意象，分手/走遠 |
| 關於妳 ___ | 12 | 回憶觸發 |
| 再煩我了 | 12 | 自我保護語氣 |
| 現在是凌晨三點 | 10 | 經典時間設定句式 |
| 過了多久 ___ | 10 | 時間流逝意象 |
| 妳就像最美的畫 | 10 | 視覺化浪漫比喻 |
| 對妳的愛不會出差錯 | 10 | 甜蜜肯定句 |

### 高頻英文詞
| 詞 | 次數 | 用法 |
|----|------|------|
| Oh | 80 | 感嘆/過渡，幾乎每首都有 |
| Baby / Girl | 各47 | 呼喚，親密感 |
| Yeah | 37 | 副歌爆發 |
| Uh | 21 | 節奏填充 |
| I / You / My | 30+ | 英文混寫增加音域 |

### 核心金句
```
「現在是凌晨三點，想妳想到失眠半夜」
「對妳的愛一直都在，像血液流淌在動脈」
「沒有妳，就不算成功」
「內心在下雨，思念像折磨」
「哪怕夕陽美如畫，但我眼裡只有她」
「能不能就放過我，我不想再為妳掉眼淚」
「被困在回憶裡面掙扎」
「曲終人散了」
「妳是那跨不過的瓶頸」
「每當我閉上眼，都是妳的畫面」
```

---

## 相似藝人

| 藝人 | 相似度 |說明 |
|------|--------|------|
| Juice Boy | ★★★★★ | 更溫柔，節奏更慢，卧室感 |
| Vigoz | ★★★★☆ | BK最常合作，旋律感強 |
| PPlin | ★★★★☆ | 相似lo-fi感，副歌更有力 |
| 8lak | ★★★☆☆ | 更實驗，氛圍更重 |
| Aioz | ★★★☆☆ | 更R&B，節奏更規整 |
| 尹熙龙 YIN. | ★★★☆☆ | 更另類，更情緒化 |
| 小姜Ginger | ★★★☆☆ | 更年輕感，vibe感 |

---

## Prompt 範例

```
幫我寫 Lo-fi R&B 中文歌詞，模仿 BK（Bill Kang）風格。

主題：[暗戀 / 失戀 / 創傷回憶 / 甜蜜浪漫]
場景：[凌晨三點 / 深夜 / 七月海風 / 晚霞]
韻腳：ang / i / ou（選一）
長度：主歌6句 + 副歌8句

要求：
- 用「妳」（非「你」）
- 8-12字/句，口語化
- 句尾押韻
- 副歌要有血液/雨/瓶頸/晚霞比喻
- 適當混入英文（Oh/Baby/Yeah）
- 避免：心碎、永遠愛你、超15字、直接說我愛你
```

---

## Repo
https://github.com/meowju/lofi-rnb-lyrics-skills
含完整 discography（50首）、style-guide、lyrics corpus（42首完整）