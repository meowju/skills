---
name: songwriting-and-ai-music
description: "Songwriting craft and Suno AI music prompts."
tags: [songwriting, music, suno, parody, lyrics, creative]
platforms: [linux, macos, windows]
triggers:
  - writing a song
  - song lyrics
  - music prompt
  - suno prompt
  - parody song
  - adapting a song
  - AI music generation
  - Taiwanese lo-fi R&B
  - BK (Bill Kang) style
  - StreetVoice lyrics
---

# Songwriting & AI Music Generation

Everything here is a GUIDELINE, not a rule. Art breaks rules on purpose.
Use what serves the song. Ignore what doesn't.

---

## 1. Song Structure (Pick One or Invent Your Own)

Common skeletons — mix, modify, or throw out as needed:

```
ABABCB  Verse/Chorus/Verse/Chorus/Bridge/Chorus    (most pop/rock)
AABA    Verse/Verse/Bridge/Verse (refrain-based)    (jazz standards, ballads)
ABAB    Verse/Chorus alternating                    (simple, direct)
AAA     Verse/Verse/Verse (strophic, no chorus)     (folk, storytelling)
```

The six building blocks:
- Intro      — set the mood, pull the listener in
- Verse      — the story, the details, the world-building
- Pre-Chorus — optional tension ramp before the payoff
- Chorus     — the emotional core, the part people remember
- Bridge     — a detour, a shift in perspective or key
- Outro      — the farewell, can echo or subvert the rest

You don't need all of these. Some great songs are just one section
that evolves. Structure serves the emotion, not the other way around.

---

## 2. Rhyme, Meter, and Sound

RHYME TYPES (from tight to loose):
- Perfect: lean/mean
- Family: crate/braid
- Assonance: had/glass (same vowels, different endings)
- Consonance: scene/when (different vowels, similar endings)
- Near/slant: enough to suggest connection without locking it down

Mix them. All perfect rhymes can sound like a nursery rhyme.
All slant rhymes can sound lazy. The blend is where it lives.

INTERNAL RHYME: Rhyming within a line, not just at the ends.
  "We pruned the lies from bleeding trees / Distilled the storm
   from entropy" — "lies/flies," "trees/entropy" create internal echoes.

METER: The rhythm of stressed vs unstressed syllables.
- Matching syllable counts between parallel lines helps singability
- The STRESSED syllables matter more than total count
- Say it out loud. If you stumble, the meter needs work
- Intentionally breaking meter can create emphasis or surprise

---

## 3. Emotional Arc and Dynamics

Think of a song as a journey, not a flat road.

ENERGY MAPPING (rough idea, not prescription):
  Intro: 2-3  |  Verse: 5-6  |  Pre-Chorus: 7
  Chorus: 8-9  |  Bridge: varies  |  Final Chorus: 9-10

The most powerful dynamic trick: CONTRAST.
- Whisper before a scream hits harder than just screaming
- Sparse before dense. Slow before fast. Low before high
- The drop only works because of the buildup
- Silence is an instrument

"Whisper to roar to whisper" — start intimate, build to full power,
strip back to vulnerability. Works for ballads, epics, anthems.

---

## 4. Writing Lyrics That Work

SHOW, DON'T TELL (usually):
- "I was sad" = flat
- "Your hoodie's still on the hook by the door" = alive
- But sometimes "I give my life" said plainly IS the power

THE HOOK:
- The line people remember, hum, repeat
- Usually the title or core phrase
- Works best when melody + lyric + emotion all align
- Place it where it lands hardest (often first/last line of chorus)

PROSODY — lyrics and music supporting each other:
- Stable feelings (resolution, peace) pair with settled melodies,
  perfect rhymes, resolved chords
- Unstable feelings (longing, doubt) pair with wandering melodies,
  near-rhymes, unresolved chords
- Verse melody typically sits lower, chorus goes higher
- But flip this if it serves the song

AVOID (unless you're doing it on purpose):
- Cliches on autopilot ("heart of gold" without earning it)
- Forcing word order to hit a rhyme ("Yoda-speak")
- Same energy in every section (flat dynamics)
- Treating your first draft as sacred — revision is creation

---

## 5. Parody and Adaptation

When rewriting an existing song with new lyrics:

THE SKELETON: Map the original's structure first.
- Count syllables per line
- Mark the rhyme scheme (ABAB, AABB, etc.)
- Identify which syllables are STRESSED
- Note where held/sustained notes fall

FITTING NEW WORDS:
- Match stressed syllables to the same beats as the original
- Total syllable count can flex by 1-2 unstressed syllables
- On long held notes, try to match the VOWEL SOUND of the original
  (if original holds "LOOOVE" with an "oo" vowel, "FOOOD" fits
   better than "LIFE")
- Monosyllabic swaps in key spots keep rhythm intact
  (Crime -> Code, Snake -> Noose)
- Sing your new words over the original — if you stumble, revise

CONCEPT:
- Pick a concept strong enough to sustain the whole song
- Start from the title/hook and build outward
- Generate lots of raw material (puns, phrases, images) FIRST,
  then fit the best ones into the structure
- If you need a specific line somewhere, reverse-engineer the
  rhyme scheme backward to set it up

KEEP SOME ORIGINALS: Leaving a few original lines or structures
intact adds recognizability and lets the audience feel the connection.

---

## 6. Suno AI Prompt Engineering

### Style/Genre Description Field

FORMULA (adapt as needed):
  Genre + Mood + Era + Instruments + Vocal Style + Production + Dynamics

```
BAD:  "sad rock song"
GOOD: "Cinematic orchestral spy thriller, 1960s Cold War era, smoky
       sultry female vocalist, big band jazz, brass section with
       trumpets and french horns, sweeping strings, minor key,
       vintage analog warmth"
```

DESCRIBE THE JOURNEY, not just the genre:
```
"Begins as a haunting whisper over sparse piano. Gradually layers
 in muted brass. Builds through the chorus with full orchestra.
 Second verse erupts with raw belting intensity. Outro strips back
 to a lone piano and a fragile whisper fading to silence."
```

TIPS:
- V4.5+ supports up to 1,000 chars in Style field — use them
- NO artist names or trademarks. Describe the sound instead.
  "1960s Cold War spy thriller brass" not "James Bond style"
  "90s grunge" not "Nirvana-style"
- Specify BPM and key when you have a preference
- Use Exclude Styles field for what you DON'T want
- Unexpected genre combos can be gold: "bossa nova trap",
  "Appalachian gothic", "chiptune jazz"
- Build a vocal PERSONA, not just a gender:
  "A weathered torch singer with a smoky alto, slight rasp,
   who starts vulnerable and builds to devastating power"

### Metatags (place in [brackets] inside lyrics field)

STRUCTURE:
  [Intro] [Verse] [Verse 1] [Pre-Chorus] [Chorus]
  [Post-Chorus] [Hook] [Bridge] [Interlude]
  [Instrumental] [Instrumental Break] [Guitar Solo]
  [Breakdown] [Build-up] [Outro] [Silence] [End]

VOCAL PERFORMANCE:
  [Whispered] [Spoken Word] [Belted] [Falsetto] [Powerful]
  [Soulful] [Raspy] [Breathy] [Smooth] [Gritty]
  [Staccato] [Legato] [Vibrato] [Melismatic]
  [Harmonies] [Choir] [Harmonized Chorus]

DYNAMICS:
  [High Energy] [Low Energy] [Building Energy] [Explosive]
  [Emotional Climax] [Gradual swell] [Orchestral swell]
  [Quiet arrangement] [Falling tension] [Slow Down]

GENDER:
  [Female Vocals] [Male Vocals]

ATMOSPHERE:
  [Melancholic] [Euphoric] [Nostalgic] [Aggressive]
  [Dreamy] [Intimate] [Dark Atmosphere]

SFX:
  [Vinyl Crackle] [Rain] [Applause] [Static] [Thunder]

Put tags in BOTH style field AND lyrics for reinforcement.
Keep to 5-8 tags per section max — too many confuses the AI.
Don't contradict yourself ([Calm] + [Aggressive] in same section).

### Custom Mode
- Always use Custom Mode for serious work (separate Style + Lyrics)
- Lyrics field limit: ~3,000 chars (~40-60 lines)
- Always add structural tags — without them Suno defaults to
  flat verse/chorus/verse with no emotional arc

---

## 7. Phonetic Tricks for AI Singers

AI vocalists don't read — they pronounce. Help them:

PHONETIC RESPELLING:
- Spell words as they SOUND: "through" -> "thru"
- Proper nouns are highest failure rate — test early
- "Nous" -> "Noose" (forces correct pronunciation)
- Hyphenate to guide syllables: "Re-search", "bio-engineering"

DELIVERY CONTROL:
- ALL CAPS = louder, more intense
- Vowel extension: "lo-o-o-ove" = sustained/melisma
- Ellipses: "I... need... you" = dramatic pauses
- Hyphenated stretch: "ne-e-ed" = emotional stretch

ALWAYS:
- Spell out numbers: "24/7" -> "twenty four seven"
- Space acronyms: "AI" -> "A I" or "A-I"
- Test proper nouns/unusual words in a short 30-second clip first
- Once generated, pronunciation is baked in — fix in lyrics BEFORE

---

## 8. Workflow

1. Write the concept/hook first — what's the emotional core?
2. If adapting, map the original structure (syllables, rhyme, stress)
3. Generate raw material — brainstorm freely before structuring
4. Draft lyrics into the structure
5. Read/sing aloud — catch stumbles, fix meter
6. Build the Suno style description — paint the dynamic journey
7. Add metatags to lyrics for performance direction
8. Generate 3-5 variations minimum — treat them like recording takes
9. Pick the best, use Extend/Continue to build on promising sections
10. If something great happens by accident, keep it

EXPECT: ~3-5 generations per 1 good result. Revision is normal.
Style can drift in extensions — restate genre/mood when extending.

---

## 9. BK / Taiwanese Lo-fi R&B Lyrics Corpus

> **Primary reference:** `references/taiwanese-lofi-rnb.md`  
> **Live corpus:** https://github.com/meowju/lofi-rnb-lyrics-skills  
> **Corpus status:** 42 complete Traditional Chinese songs (50 hot tracks total)

### Quick-Start Prompt Template (BK style)

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

風格參考（實際歌詞範例）：
「現在是凌晨三點，想妳想到失眠半夜」
「對妳的愛一直都在，像血液流淌在動脈」
「內心在下雨，思念像折磨」
「哪怕夕陽美如畫，但我眼裡只有她」
```

### 3 Proven Structural Templates

**Template A — 創傷回憶型（凌晨三點）：**
```
[時間設定] 現在是凌晨三點 → 想妳失眠
[感官觸發] 回憶環繞在周圍
[否定+崩塌] 明明說好不哭了 → 我不爭氣的哭了
[心疼句] 擔心妳沒人訴苦 / 老天也不舍告別
[崩潰點] 天空下起大雨
[迴圈重複] 現在是凌晨三點 → 回憶再現
```

**Template B — 暗戀/失戀型（給妳的愛）：**
```
[主歌1] 深夜意象 + 分開半年 + 資格喪失 × 4句
[副歌] 對妳的愛一直都在 + 血液比喻 + 翻動態 × 4句
[主歌2] 觸景傷情 + 內心下雨 × 4句
[副歌重複] + 變奏 + 自我拷問
[尾聲] 只要妳回來 + 什麼都能夠 + 成熟承諾
```

**Template C — 甜蜜浪漫型（你知道你比晚霞好看嗎）：**
```
[時間跳躍] 六月→七月牽掛→九月融洽
[引用句] 「哪怕夕陽美如畫，但我眼裡只有她」
[英文過渡] Oh Listen Baby / You drive me crazy
[承諾句] 為妳衝、為妳瘋、為妳寫浪漫情節
[生活細節] 開車/地鐵、冬天暖手/夏天加冰
[尾聲] 下輩子我的心臟依舊為妳在發燙
```

### Core Techniques (from real corpus analysis)

| 技巧 | 示例 | 效果 |
|------|------|------|
| 具象身體感受 | 「血液流淌在動脈」 | > 直接說「我想念你」100倍 |
| 自然意象比喻 | 「內心在下雨」 | > 直接說「我很傷心」10倍 |
| 反問推進情緒 | 「怎麼可能把妳忘記」 | > 直說更強烈 |
| 留白 | 「妳的畫面全都暫停了」 | > 不說想念，說畫面暫停 |
| 時空壓縮 | 「明明說好不哭了」→崩塌 | > 先否定再破防，張力更強 |
| 重複堆疊 | 「走遠 / 走遠 / 走遠」 | > 情緒加深 |
| 引用句式 | 「哪怕夕陽美如畫，但我眼裡只有她」 | > 記憶點強 |

### Key BK Data (from 42-song corpus)

- **Artist NetEase ID:** 52652468
- **Spotify:** https://open.spotify.com/artist/6oUenG9cEPeZ4QYHXZGeFN
- **YouTube:** @bkofficialmusic (70.7K subscribers)
- **Top English words:** Oh(80x), Baby/Girl(47x), Yeah(37x), Uh(21x)
- **Top 5-char phrases:** 最美的(14x), 但妳卻走遠(12x), 關於妳(12x),  現在是凌晨三點(10x)
- **Always use 「妳」 not 「你」** for love songs (0 exceptions in corpus)
- **繁體中文** — corpus is Traditional Chinese

---

## 10. Lessons Learned

- Describing the dynamic ARC in the style field matters way more
  than just listing genres. "Whisper to roar to whisper" gives
  Suno a performance map.
- Keeping some original lines intact in a parody adds recognizability
  and emotional weight — the audience feels the ghost of the original.
- The bridge slot in a song is where you can transform imagery.
  Swap the original's specific references for your theme's metaphors
  while keeping the emotional function (reflection, shift, revelation).
- Monosyllabic word swaps in hooks/tags are the cleanest way to
  maintain rhythm while changing meaning.
- A strong vocal persona description in the style field makes a
  bigger difference than any single metatag.
- Don't be precious about rules. If a line breaks meter but hits
  harder, keep it. The feeling is what matters. Craft serves art,
  not the other way around.
- For BK/Taiwanese lo-fi R&B: always use Traditional Chinese
  「妳」 not simplified 「你」 — confirmed across 42 real songs.
- The 3 structural templates (創傷回憶/暗戀失戀/甜蜜浪漫) are
  verified patterns from the real corpus — use them as starting
  scaffolds, not constraints.
