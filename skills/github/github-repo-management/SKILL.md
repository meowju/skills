---
name: github-repo-management
description: "Clone/create/fork repos; manage remotes, releases."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Repositories, Git, Releases, Secrets, Configuration]
    related_skills: [github-auth, github-pr-workflow, github-issues]
---

# GitHub Repository Management

Create, clone, fork, configure, and manage GitHub repositories. Each section shows `gh` first, then the `git` + `curl` fallback.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- **For automated/cron contexts:** GitHub PAT stored in `GH_TOKEN` env var (gh CLI does NOT persist auth in those contexts — it is NOT a reliable auth carrier for background jobs)

### Auth Detection for Automated Contexts

```bash
# gh CLI can be installed but NOT logged in — this is common in container/cron environments.
# Check auth status first, then fall back to token-based API.
if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1 | grep -q "You are logged into"; then
  AUTH="gh"
  GH_USER=$(gh api user --jq '.login')
else
  AUTH="curl"
  # Try GH_TOKEN env var first (correct for cron/background jobs)
  if [ -n "$GH_TOKEN" ]; then
    GIT_GH_TOKEN="$GH_TOKEN"
  # Then check ~/.hermes/.env
  elif [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
    GIT_GH_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
  # Then git credential helper
  elif git config credential.helper 2>/dev/null | grep -q store && echo "password" | git credential store 2>/dev/null; then
    GIT_GH_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
  fi

  if [ -z "$GIT_GH_TOKEN" ]; then
    echo "ERROR: No GitHub token available. Set GH_TOKEN env var or GITHUB_TOKEN in ~/.hermes/.env"
    return 1
  fi

  # Get username via curl
  GH_USER=$(curl -s -H "Authorization: token $GIT_GH_TOKEN" https://api.github.com/user | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])" 2>/dev/null)
fi
```

> **Cron job rule:** Never assume `gh auth login` persists across background job invocations. A cron job that succeeds once can fail the next tick because `gh` stores credentials in `~/.config/gh/` which may not be accessible from the scheduled environment. Always use `GH_TOKEN` env var for automated contexts.

If you're inside a repo already:

```bash
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

---

## 1. Cloning Repositories

Cloning is pure `git` — works identically either way:

```bash
# Clone via HTTPS (works with credential helper or token-embedded URL)
git clone https://github.com/owner/repo-name.git

# Clone into a specific directory
git clone https://github.com/owner/repo-name.git ./my-local-dir

# Shallow clone (faster for large repos)
git clone --depth 1 https://github.com/owner/repo-name.git

# Clone a specific branch
git clone --branch develop https://github.com/owner/repo-name.git

# Clone via SSH (if SSH is configured)
git clone git@github.com:owner/repo-name.git
```

**With gh (shorthand):**

```bash
gh repo clone owner/repo-name
gh repo clone owner/repo-name -- --depth 1
```

## 2. Creating Repositories

**With gh:**

```bash
# Create a public repo and clone it
gh repo create my-new-project --public --clone

# Private, with description and license
gh repo create my-new-project --private --description "A useful tool" --license MIT --clone

# Under an organization
gh repo create my-org/my-new-project --public --clone

# From existing local directory
cd /path/to/existing/project
gh repo create my-project --source . --public --push
```

**With git + curl:**

```bash
# Create the remote repo via API
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{
    "name": "my-new-project",
    "description": "A useful tool",
    "private": false,
    "auto_init": true,
    "license_template": "mit"
  }'

# Clone it
git clone https://github.com/$GH_USER/my-new-project.git
cd my-new-project

# -- OR -- push an existing local directory to the new repo
cd /path/to/existing/project
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/$GH_USER/my-new-project.git
git push -u origin main
```

To create under an organization:

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/orgs/my-org/repos \
  -d '{"name": "my-new-project", "private": false}'
```

### From a Template

**With gh:**

```bash
gh repo create my-new-app --template owner/template-repo --public --clone
```

**With curl:**

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/template-repo/generate \
  -d '{"owner": "'"$GH_USER"'", "name": "my-new-app", "private": false}'
```

## 3. Forking Repositories

**With gh:**

```bash
gh repo fork owner/repo-name --clone
```

**With git + curl:**

```bash
# Create the fork via API
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo-name/forks

# Wait a moment for GitHub to create it, then clone
sleep 3
git clone https://github.com/$GH_USER/repo-name.git
cd repo-name

# Add the original repo as "upstream" remote
git remote add upstream https://github.com/owner/repo-name.git
```

### Keeping a Fork in Sync

```bash
# Pure git — works everywhere
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

**With gh (shortcut):**

```bash
gh repo sync $GH_USER/repo-name
```

## 4. Repository Information

**With gh:**

```bash
gh repo view owner/repo-name
gh repo list --limit 20
gh search repos "machine learning" --language python --sort stars
```

**With curl:**

```bash
# View repo details
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO \
  | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(f\"Name: {r['full_name']}\")
print(f\"Description: {r['description']}\")
print(f\"Stars: {r['stargazers_count']}  Forks: {r['forks_count']}\")
print(f\"Default branch: {r['default_branch']}\")
print(f\"Language: {r['language']}\")"

# List your repos
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/user/repos?per_page=20&sort=updated" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin):
    vis = 'private' if r['private'] else 'public'
    print(f\"  {r['full_name']:40}  {vis:8}  {r.get('language', ''):10}  ★{r['stargazers_count']}\")"

# Search repos
curl -s \
  "https://api.github.com/search/repositories?q=machine+learning+language:python&sort=stars&per_page=10" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin)['items']:
    print(f\"  {r['full_name']:40}  ★{r['stargazers_count']:6}  {r['description'][:60] if r['description'] else ''}\")"
```

## 5. Repository Settings

**With gh:**

```bash
gh repo edit --description "Updated description" --visibility public
gh repo edit --enable-wiki=false --enable-issues=true
gh repo edit --default-branch main
gh repo edit --add-topic "machine-learning,python"
gh repo edit --enable-auto-merge
```

**With curl:**

```bash
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO \
  -d '{
    "description": "Updated description",
    "has_wiki": false,
    "has_issues": true,
    "allow_auto_merge": true
  }'

# Update topics
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.mercy-preview+json" \
  https://api.github.com/repos/$OWNER/$REPO/topics \
  -d '{"names": ["machine-learning", "python", "automation"]}'
```

> **GitHub App JWT → Installation Token (Node.js):** The `gh` CLI cannot be used in automated contexts for GitHub App auth — use Node.js `crypto` instead. Generation pattern: `const sign = crypto.createSign('SHA256')` → `sign.update(header + '.' + payload)` → `sign.sign(PEM)`, all base64url-encoded. Payload = `{iat, exp, iss: APP_ID}` where `iss` is the GitHub App integer ID (not the installation ID). Installation token returned as `POST /app/installations/<INSTALLATION_ID>/access_tokens` → `{token: "ghs_..."}`. Use as: `git remote set-url origin https://x-access-token:${INSTALL_TOKEN}@github.com/owner/repo.git` (Bearer NOT supported for git push with installation tokens).
>
> **GitHub App installation ID lookup:** Wrong installation ID → 404 on `POST /app/installations/<ID>/access_tokens`. Always list installations first: `GET /app/installations` returns all org/user installations with correct IDs. Common collision: `stancsz` user installation (ID: 13295359) vs `badlandslabs` org installation (ID: 135149495). Use the one matching the target repo's org/user.
>
> **GitHub App cannot create user repos:** `POST /user/repos` with a GitHub App installation token returns `403 Resource not accessible by integration` — App tokens can only write to repos the App's installation has explicit access to. Workaround: (1) create under the org where the App IS installed (e.g., `POST /orgs/meowju/repos`), (2) attempt `POST /repos/:owner/:repo/transfer` to move to user account (may also 403), or (3) fall back to token-based push with the user's PAT. Always test with a lightweight `GET /installation/repositories` first to see what the App token can actually access.

> **check_refs.py path bug (double skills/skills):** When `skills/parser/check_refs.py` calls `Path(__file__).parent.parent / "skills"`, the result is `skills/skills` because the script is already inside the `skills/` directory. Fix: `Path(__file__).parent.parent` (not `/ "skills"`). Also, the script iterates sector subdirs (e.g. `energy/`, `logistics/`) — not top-level skill dirs — so the iteration must loop over sector dirs then skill dirs inside them, not directly over `skills_root.iterdir()`.

> **Push failure with embedded-URL remotes:** GitHub has disabled password auth for HTTPS Git operations. If a remote uses `https://user:password@github.com/...` format, `git push` will fail with `Authentication failed`. The fix is to either use a token-based URL (`https://TOKEN@github.com/...`) or switch to SSH with a deploy key. The git credential helper approach (redirecting `https://github.com` to `https://swarm260219:***@github.com`) works for read operations but will fail on push. Always test push when configuring a new remote.
>
> **Repo creation: 404 vs 403 vs 409:** When creating a repo via API (`POST /user/repos` or `POST /orgs/:org/repos`) and getting a 404, the token lacks permission for that scope — check token scopes or try creating under a different org. A 409 means the repo name already exists under the authenticated user/org. A 403 means the token lacks the `repo` scope. Always decode the HTTP status before assuming the repo doesn't exist.
>
> **For org repos:** When creating a repo under an organization (not personal account), the authenticated user must have admin permission on that org. App tokens have org-level permissions that vary — confirm the App is installed on the target org with write access before attempting creation.
>
> **No gh CLI in container/cron environments:** Many container images don't have `gh` installed. The git-credential-helper redirect (`url.https://swarm260219:***@github.com.insteadof=https://github.com`) config in `~/.gitconfig` provides read access via the embedded token, but push will fail. For push access in automation, store the raw token in `GH_TOKEN` env var and use `curl` with `-u token:` for API calls.

## 6. Branch Protection

```bash
# View current protection
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection

# Set up branch protection
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["ci/test", "ci/lint"]
    },
    "enforce_admins": false,
    "required_pull_request_reviews": {
      "required_approving_review_count": 1
    },
    "restrictions": null
  }'
```

## 7. Secrets Management (GitHub Actions)

**With gh:**

```bash
gh secret set API_KEY --body "your-secret-value"
gh secret set SSH_KEY < ~/.ssh/id_rsa
gh secret list
gh secret delete API_KEY
```

**With curl:**

Secrets require encryption with the repo's public key — more involved via API:

```bash
# Get the repo's public key for encrypting secrets
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/secrets/public-key

# Encrypt and set (requires Python with PyNaCl)
python3 -c "
from base64 import b64encode
from nacl import encoding, public
import json, sys

# Get the public key
key_id = '<key_id_from_above>'
public_key = '<base64_key_from_above>'

# Encrypt
sealed = public.SealedBox(
    public.PublicKey(public_key.encode('utf-8'), encoding.Base64Encoder)
).encrypt('your-secret-value'.encode('utf-8'))
print(json.dumps({
    'encrypted_value': b64encode(sealed).decode('utf-8'),
    'key_id': key_id
}))"

# Then PUT the encrypted secret
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/secrets/API_KEY \
  -d '<output from python script above>'

# List secrets (names only, values hidden)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/secrets \
  | python3 -c "
import sys, json
for s in json.load(sys.stdin)['secrets']:
    print(f\"  {s['name']:30}  updated: {s['updated_at']}\")"
```

Note: For secrets, `gh secret set` is dramatically simpler. If setting secrets is needed and `gh` isn't available, recommend installing it for just that operation.

## 8. Releases

**With gh:**

```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release create v2.0.0-rc1 --draft --prerelease --generate-notes
gh release create v1.0.0 ./dist/binary --title "v1.0.0" --notes "Release notes"
gh release list
gh release download v1.0.0 --dir ./downloads
```

**With curl:**

```bash
# Create a release
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/releases \
  -d '{
    "tag_name": "v1.0.0",
    "name": "v1.0.0",
    "body": "## Changelog\n- Feature A\n- Bug fix B",
    "draft": false,
    "prerelease": false,
    "generate_release_notes": true
  }'

# List releases
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/releases \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin):
    tag = r.get('tag_name', 'no tag')
    print(f\"  {tag:15}  {r['name']:30}  {'draft' if r['draft'] else 'published'}\")"

# Upload a release asset (binary file)
RELEASE_ID=<id_from_create_response>
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/octet-stream" \
  "https://uploads.github.com/repos/$OWNER/$REPO/releases/$RELEASE_ID/assets?name=binary-amd64" \
  --data-binary @./dist/binary-amd64
```

## 9. GitHub Actions Workflows

**With gh:**

```bash
gh workflow list
gh run list --limit 10
gh run view <RUN_ID>
gh run view <RUN_ID> --log-failed
gh run rerun <RUN_ID>
gh run rerun <RUN_ID> --failed
gh workflow run ci.yml --ref main
gh workflow run deploy.yml -f environment=staging
```

**With curl:**

```bash
# List workflows
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/workflows \
  | python3 -c "
import sys, json
for w in json.load(sys.stdin)['workflows']:
    print(f\"  {w['id']:10}  {w['name']:30}  {w['state']}\")"

# List recent runs
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?per_page=10" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin)['workflow_runs']:
    print(f\"  Run {r['id']}  {r['name']:30}  {r['conclusion'] or r['status']}\")"

# Download failed run logs
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs

# Re-run a failed workflow
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/rerun

# Re-run only failed jobs
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/rerun-failed-jobs

# Trigger a workflow manually (workflow_dispatch)
WORKFLOW_ID=<workflow_id_or_filename>
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/workflows/$WORKFLOW_ID/dispatches \
  -d '{"ref": "main", "inputs": {"environment": "staging"}}'
```

## 10. Gists

**With gh:**

```bash
gh gist create script.py --public --desc "Useful script"
gh gist list
```

**With curl:**

```bash
# Create a gist
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/gists \
  -d '{
    "description": "Useful script",
    "public": true,
    "files": {
      "script.py": {"content": "print(\"hello\")"}
    }
  }'

# List your gists
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/gists \
  | python3 -c "
import sys, json
for g in json.load(sys.stdin):
    files = ', '.join(g['files'].keys())
    print(f\"  {g['id']}  {g['description'] or '(no desc)':40}  {files}\")"
```

## Quick Reference Table

| Action | gh | git + curl |
|--------|-----|-----------|
| Clone | `gh repo clone o/r` | `git clone https://github.com/o/r.git` |
| Create repo | `gh repo create name --public` | `curl POST /user/repos` |
| Fork | `gh repo fork o/r --clone` | `curl POST /repos/o/r/forks` + `git clone` |
| Repo info | `gh repo view o/r` | `curl GET /repos/o/r` |
| Edit settings | `gh repo edit --...` | `curl PATCH /repos/o/r` |
| Create release | `gh release create v1.0` | `curl POST /repos/o/r/releases` |
| List workflows | `gh workflow list` | `curl GET /repos/o/r/actions/workflows` |
| Rerun CI | `gh run rererun ID` | `curl POST /repos/o/r/actions/runs/ID/rerun` |
| Set secret | `gh secret set KEY` | `curl PUT /repos/o/r/actions/secrets/KEY` (+ encryption) |

## Pre-Push Safety Checks (MUST run before `git push`)

**Lesson learned 2026-06-01:** User said "commit and push those skills to repo X" — but the local `git` repo was actually rooted at `/opt/data` (parent of `skills/`), had 247 pending changes including `.env`, `github-app.pem`, `auth.json`, `config.yaml`, `cron/`, and had no remote configured. A naive `git add . && git commit && git push` would have leaked the GitHub App private key to a public/private org repo.

**Always run this 4-check sequence before any push:**

```bash
# 1. Where is the actual git root? (might surprise you — worktrees, subdirs)
cd /path/where/you/think/the/repo/is
git rev-parse --show-toplevel
git config --get core.worktree 2>/dev/null  # worktree check

# 2. What's pending? (count + first 30 files)
git status --short | wc -l
git status --short | head -30

# 3. Are any obvious secrets pending? — these MUST NEVER be committed
git status --short | grep -iE '\.(env|pem|key)$|/auth\.json|/config\.yaml$|\.lock$|/cron/|/bin/|gateway' && echo "🚨 SECRETS DETECTED" || echo "no obvious secrets"

# 4. Is there a remote at all? (a no-remote repo shouldn't be pushed without thinking)
git remote -v
```

**Decision matrix after the checks:**

| Finding | Action |
|---------|--------|
| Git root is larger than the dir you wanted to push | STOP. Use a temporary clean `git init` directory with `cp -r` of just the files you need, then push that. |
| `wc -l` ≥ 10 and not all the files you intended | STOP. Surface to user with `git status --short \| head -30` before any commit. Use a 4-option `clarify`: (a) push only intended files discarding the rest, (b) push full subdir to repo's `skills/` subfolder, (c) commit-and-push all 247 (not recommended), (d) wait for user. |
| Secret-looking files in pending changes | NEVER proceed without user confirmation. Show the matching file paths. |
| No remote configured | The repo has never been pushed. Confirm intended remote with user before `git remote add`. |
| Remote exists but you haven't verified App has push permission on it | See the GitHub App section above — run the `permissions` check before `git push`. |

**Clean subdir-only push pattern** (when you want to push `skills/ai-money-maker/` but the working tree has 247 other changes):

```bash
# Make a temp dir, copy ONLY the files you want, push from there
WORK=/tmp/skill-push-$$
mkdir -p $WORK
cp -r /opt/data/skills/productivity/ai-money-maker $WORK/
cp -r /opt/data/skills/productivity/breakup-recovery $WORK/
cp -r /opt/data/skills/productivity/purpose-finder $WORK/
cp -r /opt/data/skills/productivity/wealth-mindset $WORK/
cd $WORK
git init -q
git config user.email "agent@hermes.local"
git config user.name "hermes-agent"
git add -A
git commit -q -m "Add 4 skills: ai-money-maker, breakup-recovery, purpose-finder, wealth-mindset"
git remote add origin https://x-access-token:${INSTALL_TOKEN}@github.com/badlandslabs/agent-skills.git
git push -u origin main
# Clean up
rm -rf $WORK
```
