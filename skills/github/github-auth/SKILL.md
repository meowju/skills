---
name: github-auth
description: "GitHub auth setup: HTTPS tokens, SSH keys, gh CLI login."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Authentication, Git, gh-cli, SSH, Setup]
    related_skills: [github-pr-workflow, github-code-review, github-issues, github-repo-management]
---

# GitHub Authentication Setup

This skill sets up authentication so the agent can work with GitHub repositories, PRs, issues, and CI. It covers two paths:

- **`git` (always available)** — uses HTTPS personal access tokens or SSH keys
- **`gh` CLI (if installed)** — richer GitHub API access with a simpler auth flow

## Detection Flow

When a user asks you to work with GitHub, run this check first:

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"

# Check if already authenticated
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"
```

**Decision tree:**
1. If `gh auth status` shows authenticated → you're good, use `gh` for everything
2. If `gh` is installed but not authenticated → use "gh auth" method below
3. If `gh` is not installed → use "git-only" method below (no sudo needed)

### ⚠️ Critical: gh CLI Does NOT Persist Auth in Cron/Background Contexts

> **gh CLI stores credentials in `~/.config/gh/hosts.yml`** — this file may not be accessible from a scheduled/cron environment (different user, container boundary, WSL interop issue). A `gh auth status` that succeeds in an interactive session will fail in a cron job even though the token is "valid."

**For ANY automated context (cron jobs, background scripts, CI, scheduled tasks):**
- Always set `GH_TOKEN` env var with the PAT
- Do NOT rely on `gh auth status` passing in a cron job to assume gh is usable
- Use `curl` with `Authorization: token $GH_TOKEN` for API calls in automated contexts

Correct pattern for cron jobs:
```bash
if [ -n "$GH_TOKEN" ]; then
  # Use token-based API (correct for cron/background)
  curl -s -H "Authorization: token $GH_TOKEN" https://api.github.com/user
else
  # Interactive session — try gh
  GH_USER=$(gh api user --jq '.login')
fi
```

The `github-repo-management` skill has the full auth detection script for automated contexts — load it when setting up cron jobs that push to GitHub.

---

## Method 1: Git-Only Authentication (No gh, No sudo)

This works on any machine with `git` installed. No root access needed.

### Option A: HTTPS with Personal Access Token (Recommended)

This is the most portable method — works everywhere, no SSH config needed.

**Step 1: Create a personal access token**

Tell the user to go to: **https://github.com/settings/tokens**

- Click "Generate new token (classic)"
- Give it a name like "hermes-agent"
- Select scopes:
  - `repo` (full repository access — read, write, push, PRs)
  - `workflow` (trigger and manage GitHub Actions)
  - `read:org` (if working with organization repos)
- Set expiration (90 days is a good default)
- Copy the token — it won't be shown again

**Step 2: Configure git to store the token**

```bash
# Set up the credential helper to cache credentials
# "store" saves to ~/.git-credentials in plaintext (simple, persistent)
git config --global credential.helper store

# Now do a test operation that triggers auth — git will prompt for credentials
# Username: <their-github-username>
# Password: <paste the personal access token, NOT their GitHub password>
git ls-remote https://github.com/<their-username>/<any-repo>.git
```

After entering credentials once, they're saved and reused for all future operations.

**Alternative: cache helper (credentials expire from memory)**

```bash
# Cache in memory for 8 hours (28800 seconds) instead of saving to disk
git config --global credential.helper 'cache --timeout=28800'
```

**Alternative: set the token directly in the remote URL (per-repo)**

```bash
# Embed token in the remote URL (avoids credential prompts entirely)
git remote set-url origin https://<username>:<token>@github.com/<owner>/<repo>.git
```

**Step 3: Configure git identity**

```bash
# Required for commits — set name and email
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

**Step 4: Verify**

```bash
# Test push access (this should work without any prompts now)
git ls-remote https://github.com/<their-username>/<any-repo>.git

# Verify identity
git config --global user.name
git config --global user.email
```

### Option B: SSH Key Authentication

Good for users who prefer SSH or already have keys set up.

**Step 1: Check for existing SSH keys**

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || echo "No SSH keys found"
```

**Step 2: Generate a key if needed**

```bash
# Generate an ed25519 key (modern, secure, fast)
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519 -N ""

# Display the public key for them to add to GitHub
cat ~/.ssh/id_ed25519.pub
```

Tell the user to add the public key at: **https://github.com/settings/keys**
- Click "New SSH key"
- Paste the public key content
- Give it a title like "hermes-agent-<machine-name>"

**Step 3: Test the connection**

```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

**Step 4: Configure git to use SSH for GitHub**

```bash
# Rewrite HTTPS GitHub URLs to SSH automatically
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

**Step 5: Configure git identity**

```bash
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

---

## Method 2: gh CLI Authentication

If `gh` is installed, it handles both API access and git credentials in one step.

### Interactive Browser Login (Desktop)

```bash
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser
```

### Manual Binary Install (no apt, no sudo, no npm -g)

When `gh` is not in PATH and cannot be installed via package managers:

```bash
# 1. Download the latest release tarball
curl -fsSL https://github.com/cli/cli/releases/download/v2.63.2/gh_2.63.2_linux_amd64.tar.gz \
  -o /tmp/gh.tar.gz

# 2. Extract to /tmp/
tar -xzf /tmp/gh.tar.gz -C /tmp/

# 3. Move binary to user's local bin (must be in PATH)
mv /tmp/gh_2.63.2_linux_amd64/bin/gh ~/local/bin/gh
chmod +x ~/local/bin/gh

# 4. Verify
~/local/bin/gh version
```

**Note:** Replace `v2.63.2` with the current release version from https://github.com/cli/cli/releases/latest

**Troubleshooting npm-installed gh breakage:** If `npm install -g gh` produced a broken `gh` (TypeError about `options`), remove it and use the manual binary install above:
```bash
npm uninstall -g gh
npm install -g gh --prefix ~/local   # OR use manual method above
```

### Token-Based Login (Headless / SSH Servers)

```bash
echo "<THEIR_TOKEN>" | gh auth login --with-token

# Set up git credentials through gh
gh auth setup-git
```

### Verify

```bash
gh auth status
```

---

## Using the GitHub API Without gh

When `gh` is not available, you can still access the full GitHub API using `curl` with a personal access token. This is how the other GitHub skills implement their fallbacks.

### Setting the Token for API Calls

```bash
# Option 1: Export as env var (preferred — keeps it out of commands)
export GITHUB_TOKEN="<token>"

# Then use in curl calls:
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

### Extracting the Token from Git Credentials

If git credentials are already configured (via credential.helper store), the token can be extracted:

```bash
# Read from git credential store
grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|'
```

### Helper: Detect Auth Method

Use this pattern at the start of any GitHub workflow:

```bash
# Try gh first, fall back to git + curl
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  echo "AUTH_METHOD=gh"
elif [ -n "$GITHUB_TOKEN" ]; then
  echo "AUTH_METHOD=curl"
elif [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
  export GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
  echo "AUTH_METHOD=curl"
elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
  export GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
  echo "AUTH_METHOD=curl"
else
  echo "AUTH_METHOD=none"
  echo "Need to set up authentication first"
fi
```

---

## Method 3: GitHub App Authentication (JWT + Installation Token)

Use this when the user has a GitHub App registered (e.g., `meowju` with App ID `3737759`) and the repo is private/organizational. This method avoids PAT expiry issues — installation tokens are short-lived but can be refreshed.

**Requirements:**
- GitHub App private key file (PEM)
- App ID
- Installation ID for the target org/user

**Step 1: Generate JWT (Node.js)**

```bash
JWT=$(node -e "
const crypto = require('crypto');
const fs = require('fs');
const privateKey = fs.readFileSync('/path/to/github-app.pem', 'utf8');
const appId = 'YOUR_APP_ID';
const now = Math.floor(Date.now() / 1000);
function base64url(str) {
  return Buffer.from(JSON.stringify(str)).toString('base64')
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
const header = base64url({ typ: 'JWT', alg: 'RS256' });
const payload = base64url({ iat: now, exp: now + 600, iss: appId });
const sign = crypto.createSign('SHA256');
sign.write(header + '.' + payload); sign.end();
const sig = sign.sign(privateKey, 'base64')
  .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
console.log(header + '.' + payload + '.' + sig);
")
```

**Step 2: Find the correct installation ID**

The installation ID is NOT the same as the App ID. List all installations for the app:
```bash
curl -s -H "Authorization: Bearer $JWT" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/app/installations | node -e "
const data = JSON.parse(require('fs').readFileSync(0, 'utf8'));
data.forEach(i => console.log(i.id, i.account.login, '(', i.repository_selection, ')'));
"
```

Find the row where `account.login` matches the target org/user. The numeric ID is the installation ID.

> ⚠️ **Common mistake**: Using the user's installation ID (stancsz user = `13295359`) for an org repo (`badlandslabs`). The org has its own installation ID (`135149495`). If you get `404 Not Found` on `POST /app/installations/<ID>/access_tokens`, check the correct installation ID.

**Step 3: Get installation access token**

```bash
INSTALL_TOKEN=$(curl -s -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/app/installations/<INSTALLATION_ID>/access_tokens \
  | node -e "const d=JSON.parse(require('fs').readFileSync(0,'utf8')); console.log(d.token || console.error(JSON.stringify(d)))")
```

**Step 4: Push with the installation token**

```bash
cd /path/to/repo
git remote set-url origin https://x-access-token:$INSTALL_TOKEN@github.com/<owner>/<repo>.git
git push origin main
```

> ⚠️ **Note**: `x-access-token:` is the literal username prefix, not a placeholder. GitHub requires this exact format for installation token auth over HTTPS.

**Verification:**
```bash
curl -s -H "Authorization: token $INSTALL_TOKEN" \
  https://api.github.com/repos/<owner>/<repo> | node -e "
const d = JSON.parse(require('fs').readFileSync(0, 'utf8'));
console.log(d.full_name, '| private:', d.private, '| pushed:', d.pushed_at);
"
```

> 📎 **For stancsz's meowju App:** see `references/meowju-app-installations.md` for the verified installation ID table (re-verify before each use; IDs go stale).

### Pitfalls for GitHub App Auth

- **Wrong installation ID** → `404 Not Found` on access token endpoint. List installations first to find the correct one. **Memory drift is real**: a previously-cached installation ID (e.g. `135149495` for `badlandslabs`) can be re-issued by GitHub (actual `137093171` as of 2026-06) without notice. Always re-list before generating tokens, do not trust cached IDs in memory or notes.
- **Expired JWT** → JWT has 10-minute TTL. Generate fresh before each use.
- **Token expires during push** → Installation tokens expire. For long pushes, ensure the token is still valid or re-fetch.
- **Installation has `repository_selection: selected`** → The app only has access to repos explicitly granted. Check that the target repo is selected in the GitHub App settings.
- **App has no permission on the target repo** (NEW, see 2026-06-01 session) → Token generates fine, but `GET /repos/{owner}/{repo}` returns `permissions: {admin:False, maintain:False, push:False, triage:False, pull:False}`. Push will be rejected with `403` even though the token is valid. **Always verify permission scope on the target repo BEFORE generating the install token and before any push.** If the App wasn't granted access to that repo at install time, the only fix is for the user to go to https://github.com/apps/{app-slug}/installations/{id} → Repository access → add the repo. Agent cannot self-fix this.

**Pre-push verification snippet (run after getting the install token, BEFORE any push):**
```bash
curl -s -H "Authorization: token $INSTALL_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO | \
  node -e "const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
           const p=d.permissions||{};
           if (!p.push && !p.maintain && !p.admin) {
             console.error('STOP: App has no push permission on '+d.full_name);
             console.error('  permissions:', JSON.stringify(p));
             console.error('  User must grant access at: https://github.com/apps/{app-slug}/installations/{installation_id}');
             process.exit(2);
           } else { console.log('OK: push allowed, perms:', JSON.stringify(p)); }"
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | GitHub disabled password auth. Use a personal access token as the password, or switch to SSH |
| `remote: Permission to X denied` | Token may lack `repo` scope — regenerate with correct scopes |
| `fatal: Authentication failed` | Cached credentials may be stale — run `git credential reject` then re-authenticate |
| `ssh: connect to host github.com port 22: Connection refused` | Try SSH over HTTPS port: add `Host github.com` with `Port 443` and `Hostname ssh.github.com` to `~/.ssh/config` |
| Credentials not persisting | Check `git config --global credential.helper` — must be `store` or `cache` |
| Multiple GitHub accounts | Use SSH with different keys per host alias in `~/.ssh/config`, or per-repo credential URLs |
| `gh: command not found` + no sudo | Use git-only Method 1 above — no installation needed |
