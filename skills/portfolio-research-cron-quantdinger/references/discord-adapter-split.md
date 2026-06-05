# Discord Adapter Split Behavior — Reference for Cron Markdown Reports

Last verified: 2026-06-02 against `/opt/hermes/gateway/platforms/discord.py` and
`/opt/hermes/gateway/platforms/base.py`.

## Hard limits

- `MAX_MESSAGE_LENGTH = 2000` (Discord.py, line ~547 of discord.py)
- `_SPLIT_THRESHOLD = 1900` — chunk body budget is reduced by ~100 chars to
  leave room for ` (1/3)` style indicators and code-fence open/close pairs.

## Split algorithm (base.py `truncate_message`)

When the final response is over 2000 chars, the adapter splits it into
multiple Discord messages and posts them sequentially (with `(1/3)` indicators).

The split prefers:
1. Newline (`\n`) at or before position 1900
2. Space at or before position 1900
3. Hard cut at 1900 if neither exists

It also handles inline code spans (`` ` ``) — refuses to split inside one
because MarkdownV2 parsers break on unpaired backticks. (Telegram cares;
Discord tolerates them, but the adapter is conservative.)

## Implication for cron report design

For a markdown report destined for Discord:

- **Anything that MUST reach the user (signal table, portfolio P&L) goes
  first.**
- **Complementary content (news, secondary notes) goes at the END** so
  that if the scheduler truncates, the essential block survives in
  chunk 1.
- **Hard cap total report length to ~3900 chars** → 2-3 chunks, no
  scroll-back needed.

## Verified good layouts for this codebase

| Layout | Report size | Splits into |
|---|---|---|
| Market + Ranking + Portfolio + Notes + Risk + Footer + 7 news | ~3900 | 3 chunks, news at tail |
| Same without news | ~3300 | 2 chunks |

The 3-chunk split is acceptable — users see the most important data
first, and the full report is always preserved in the saved `.md` file
under `~/./cron/output/f2f177230acb/`.

## Patterns that BITE

- **Putting news in the middle of a 5000-char report** → Discord splits
  between news headlines, leaving an orphan "10m ago — [" hanging at
  the end of a chunk. Always place lengthy complementary blocks at the
  end.
- **Assuming Discord adapter will wrap long content gracefully** — it
  won't. Long lines without spaces can exceed 1900 and trigger a
  hard mid-word cut.
- **Putting a single line of news after the closing `---` of the
  footer** — looks tidy, but the adapter doesn't care about your
  semantics; it splits on `\n`/space position.
