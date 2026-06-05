# meowju GitHub App — Installation Reference (stancsz)

Verified 2026-06-01 via `GET /app/installations` with App ID `3737759` JWT.
**Always re-verify before use** — GitHub re-issues installation IDs without notice and cached values in memory go stale (e.g. `135149495` was wrong by 2026-06, actual is `137093171`).

| Installation ID | Account | Type | repository_selection | Notes |
|-----------------|---------|------|----------------------|-------|
| `137093171` | `badlandslabs` | Organization | `all` | Default for stancsz's org repos |
| `136247983` | `meowju` | Organization | `all` | App's own org |
| `133212190` | `ba-research` | Organization | `all` | |
| `133202684` | `deeptendies` | Organization | `all` | |
| `133202598` | `wellframe-ba` | Organization | `all` | |
| `132953859` | `stancsz` | User | `selected` | User-level install — DIFFERENT from `13295359` (note the extra `8`) |
| `132953802` | `meow-granville` | Organization | `all` | |

**Common-confusion installations to avoid:**

- `135149495` — appeared in earlier memory notes for `badlandslabs`, but was stale by 2026-06. Returns `404 Not Found` on `POST /app/installations/135149495/access_tokens`. Use `137093171` instead.
- `13295359` — looks like the stancsz user install (5 digits) but is wrong. Correct is `132953859` (6 digits). Easy to misread.

**Verification pattern** (always run before generating a token):

```python
import jwt, time
from cryptography.hazmat.primitives import serialization
key = serialization.load_pem_private_key(open("/opt/data/github-app.pem","rb").read(), password=None)
app_jwt = jwt.encode({"iat": int(time.time())-60, "exp": int(time.time())+600, "iss":"3737759"},
                     key, algorithm="RS256")
# List installations, then for the matching account.login, capture id
```

**Path the user must go to when the App lacks permission on a repo:**
`https://github.com/apps/meowju/installations/{installation_id}` → Repository access → add the target repo.
