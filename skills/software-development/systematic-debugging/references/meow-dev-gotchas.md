# meow-swarm Development Gotchas

Reference patterns for working with meow-swarm source. Add new patterns as discovered.

---

## Missing runtime dep after `git pull`

**Symptom:** `node dist/bin/meow.js` crashes with `ERR_MODULE_NOT_FOUND: Cannot find package '@xenova/transformers'`.

**Root cause:** `package.json` lists the package in `dependencies`, but `npm install` was not run after pulling new commits, or a fresh clone didn't `npm install`.

**Fix:**
```bash
npm install
npm run build
```

**Verification:**
```bash
node dist/bin/meow.js -p "echo hello"  # should not exit 124
```

---

## Extension discovery throws ERR_UNKNOWN_FILE_EXTENSION

**Symptom:** `Failed to discover extension at /path/to/extension.ts: TypeError [ERR_UNKNOWN_FILE_EXTENSION]: Unknown file extension ".ts"`

**Context:** This happens when running from **source** (`npx tsx src/index.ts`) because Node.js ESM can't import `.ts` files directly. The built `dist/` output handles extensions correctly.

**Fix in source (ExtensionManager.ts):**
```typescript
catch (e: any) {
  if (
    e.code === "ERR_MODULE_NOT_FOUND" ||
    e.code === "ERR_UNKNOWN_FILE_EXTENSION" ||  // <-- add this
    e.message?.includes("Cannot find module")
  ) {
    // Skip — module will be loaded from dist/ built output instead
  } else {
    console.error(`Failed to discover extension at ${file}:`, e);
  }
}
```

**Key insight:** The extension error is **expected and harmless** when running from source. It does NOT cause the program to crash — only the extension discovery fails silently, which is correct behavior.

---

## `npm run dev` (tsx) works but `node dist/bin/meow.js` ECONNREFUSED

**Symptom:** `npx tsx src/index.ts -p "..."` works. `node dist/bin/meow.js -p "..."` fails with `ECONNREFUSED` (connection refused to LLM API).

**Root cause:** Environment variables not loaded. `tsx src/index.ts` uses the `.env` in the repo via the tsx process, but running `node dist/bin/meow.js` directly doesn't source `.env`.

**Fix:**
```bash
source ~/.env   # or: export $(cat ~/.env | grep -v '^#' | xargs)
node dist/bin/meow.js -p "echo hello"
```

**Best practice:** Always source `.env` before running the built binary:
```bash
source ~/.env && node dist/bin/meow.js -p "your task"
```

Or use the `npm run dev` path which inherits the shell's env.

---

## meow setup after fresh pull

Full setup sequence after syncing with upstream:

```bash
git fetch origin
git log HEAD..origin/main --oneline  # see new commits

git stash     # if you have local untracked files
git pull origin main
git stash pop

npm install
npm run build

# set env
source ~/.env
```

---

## gh CLI manual install (no apt/sudo)

When gh is not in PATH and can't be installed via package manager:

```bash
# Download release
curl -fsSL https://github.com/cli/cli/releases/download/v2.63.2/gh_2.63.2_linux_amd64.tar.gz \
  -o /tmp/gh.tar.gz

# Extract
tar -xzf /tmp/gh.tar.gz -C /tmp/

# Move binary to ~/local/bin/
mv /tmp/gh_2.63.2_linux_amd64/bin/gh ~/local/bin/gh
chmod +x ~/local/bin/gh

# Verify
~/local/bin/gh version
```