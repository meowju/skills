# WSL Cron Path Resolution — Permanent Note

## The Problem

In WSL, `os.path.expanduser("~/")` resolves based on the **effective user's home**, not the WSL host's view of where Hermes is installed.

- Cron job runs as user `hermes`
- `HOME=/opt/data/home` (not `/opt/hermes`)
- `~/./cron/output/` → `/opt/data/home/cron/output/`
- But the SKILL.md previously documented `/opt/hermes/cron/output/` — which is the host's symlink path, inaccessible from inside WSL to the hermes user

## Verification Command

```bash
python -c "import os; print(os.path.expanduser('~/./cron/output/'))"
# Expected: /opt/data/home/cron/output/
```

## Always-Use Pattern

```python
# In any cron/research script — do NOT use ~/ or os.path.expanduser('~/')
# The Hermes cron scheduler resolves paths relative to /opt/hermes/ (hermes home)
# The scheduler MONITORS /opt/hermes/cron/output/f2f177230acb/ for discord_msg_*.txt
out_dir = "/opt/hermes/cron/output/f2f177230acb"
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, f"portfolio-research-{ts}.md")
discord_file = os.path.join(out_dir, f"discord_msg_{ts}.txt")
```

**Path history:** Previously documented `/opt/data/home/cron/output/` — that is WRONG. The scheduler only auto-delivers Discord messages from `/opt/hermes/cron/output/f2f177230acb/`. Verified May 30 and Jun 1, 2026 sessions both confirmed the correct path.

## Why This Matters

The cron job runs silently every 15 minutes with no user present. If the path is wrong, the report is silently discarded and no one knows. This is a **silent failure mode** — the script completes with exit code 0 and no error is visible. Always use absolute paths in automated scripts.

## Related: Output Dir vs Source Dir

The source script `cron_research.py` lives at `/opt/data/agentictendies/cron_research.py`. The output goes to `/opt/data/home/cron/output/`. These are intentionally separate — source code stays in `agentictendies/` and generated reports go to `home/cron/output/`.