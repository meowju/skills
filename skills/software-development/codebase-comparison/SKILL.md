---
name: codebase-comparison
description: "Compare two codebases — study a reference (or #1 on GitHub), find what the target is missing, and port the valuable parts."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [codebase-analysis, comparison, feature-migration, code-study, github-research, knowledge-transfer]
    related_skills: [spike, writing-plans, subagent-driven-development]
---

# Codebase Comparison — Study Reference → Port to Target

## When to Use

Use when the user says things like:
- "Research X, #1 on GitHub — our Y is similar. Clone it, study it, take what Y doesn't have."
- "Compare A vs B — what's A missing?"
- "Port feature F from project P to our project Q"
- "Study this reference implementation and tell me what we should adopt"

**Not for:**
- Quick one-off questions answerable from README (just research, don't clone)
- Simple refactoring within one codebase (use spike or writing-plans instead)
- Tasks that are already well-scoped and don't need cross-project knowledge transfer

## Core Pattern

```
1. Clone both repos (reference + target) to /opt/data/<name>
2. Explore structure: entry points, key modules, architecture docs
3. Study reference's core mechanisms in depth
4. Compare: what does reference have that target lacks?
5. Evaluate each gap: worth porting? difficulty? priority?
6. Optionally: write ported code for high-value gaps
```

## Step-by-Step

### 1. Clone Both Repos

```bash
# Reference (the #1 / source of learning)
git clone --depth=1 https://github.com/USER/REFERENCE /opt/data/reference

# Target (the project to upgrade)
git clone https://github.com/USER/TARGET /opt/data/target
# or if already cloned: just use existing path
```

Use `--depth=1` for reference (just need latest), full clone for target (may need history/branches).

### 2. Explore Structure

```bash
# List all source files (exclude vendor/node_modules/dist)
find /opt/data/REFERENCE -type f -name "*.ts" -o -name "*.py" -o -name "*.js" | \
  grep -v node_modules | grep -v dist | sort | less

# Read architecture docs
cat REFERENCE/README.md | head -150
cat REFERENCE/ARCHITECTURE.md 2>/dev/null || cat REFERENCE/docs/architecture.md 2>/dev/null

# Find entry points
ls REFERENCE/src/ 2>/dev/null
ls REFERENCE/bin/ 2>/dev/null
```

### 3. Study Reference's Core Mechanisms

Focus on what the reference does **well and uniquely**. Key areas to investigate (in priority order):

| Area | What to look for |
|------|-----------------|
| **Orchestration / Agent system** | How does it coordinate multiple agents? What topologies? How does it handle failures? |
| **Memory / RAG** | How does it store and retrieve knowledge? What backends? Vector search? |
| **Quality / Convergence** | How does it detect done? What gates? Self-review loops? |
| **Self-learning / Adaptation** | Does it learn from outcomes? Persistent patterns? Feedback loops? |
| **Plugin / Extension system** | How are capabilities extended? What's the plugin API? |
| **Resilience patterns** | Retry? Circuit breaker? Bulkhead? Rate limiting? |
| **Event system** | Event sourcing? Audit trail? Domain events? |
| **MCP integration** | How does it expose tools via MCP? |

### 4. Compare with Target

```bash
# What are target's key files?
ls /opt/data/target/src/

# Find feature gaps by checking what reference has that target doesn't
# Reference has X: does target have X?
find /opt/data/target/src -name "*event*"  # event system?
find /opt/data/target/src -name "*hook*"   # hooks?
find /opt/data/target/src -name "*resilience*"  # resilience?

# Compare similar modules
diff /opt/data/reference/src/orchestrator/Orchestrator.ts \
     /opt/data/target/src/orchestrator/Orchestrator.ts 2>/dev/null || echo "files differ"
```

### 5. Evaluate Gaps — The Comparison Table

For each gap found, assess:

| Gap | Reference does | Target does | Worth移植？ | 难度 | 优先级 |
|-----|---------------|------------|------------|------|--------|
| Event Sourcing | Full append-only event log | None | ✅ High | Medium | P1 |
| Hooks System | 17 hook points | None | ✅ High | Low | P1 |
| Circuit Breaker | Retry + CB + Bulkhead | Basic retry | ✅ Medium | Low | P2 |

**Worth移植判断标准：**
- ✅ **High**: Unique capability that target lacks entirely; clearly superior approach; low implementation risk
- ⚠️ **Medium**: Improvement but target has something comparable; moderate effort
- ❌ **Low**: Marginal improvement; high complexity; or target already does it adequately

### 6. Port High-Value Features

For each P1 gap, create the ported file in target:

```
target/src/[area]/[feature].ts
```

**Porting principles:**
1. Write the file directly in target repo — don't delegate to subagent (subagent API fails on heavy cloning/traversal)
2. Adapt to target's coding style, imports, and conventions
3. Include a docstring citing the source and what was adapted
4. Write tests if target has a test convention

### Patching Existing Target Files (not just creating new ones)

When the target already has a file that needs enhancement (e.g., `Orchestrator.ts` already exists), use `patch` (targeted find-replace) rather than rewriting the whole file:

```bash
# Read the target file in chunks to understand its structure
cat /opt/data/target/src/orchestrator/Orchestrator.ts | head -120  # imports + class fields
# then read from offset 100 onwards for constructor and methods

# Use patch with enough context to uniquely identify the target region
patch(
  old_string: "// EXACT TEXT FROM FILE including surrounding context",
  new_string: "// NEW TEXT that replaces the old"
)
```

**Order for patching an existing file:**
1. Read first ~100 lines → add new imports
2. Read constructor section → add new class fields + initialization
3. Read each method that needs enhancement → patch it in place
4. Add new public methods at the end

**Key insight:** `patch` requires exact text matching. Read the file with `offset`/`limit` to get the exact text (including whitespace, indentation) before patching. Do not guess — always read first.

### Reference Repo Monorepo Navigation

Reference repos like ruflo v3 use monorepo structure:
```
ruflo/
  v3/
    @claude-flow/
      swarm/src/        # agent orchestration
      memory/src/        # RAG/memory
      shared/src/        # types, hooks, resilience, plugins
      mcp/               # MCP protocol
      cli/src/commands/  # 26 CLI commands
      browser/src/       # browser automation
```

Discover the actual structure:
```bash
ls /opt/data/ruflo/v3/
ls /opt/data/ruflo/v3/@claude-flow/
find /opt/data/ruflo/v3 -maxdepth 3 -name "*.ts" | grep -v node_modules | grep -v dist | head -30
```

## Example: meow (target) vs ruflo v3 (reference)

The meow→ruflow study produced 9 new files in target (meow), organized by area:

**Orchestrator layer (`src/orchestrator/`):**
- `EventStore.ts` ← ADR-007 event sourcing (append-only JSONL)
- `Hooks.ts` ← 17 hook points (PreToolUse, PostFileWrite, AgentFailed, etc.)
- `Resilience.ts` ← Retry + CircuitBreaker + Bulkhead patterns
- `ConsensusEngine.ts` ← Raft / Byzantine / Gossip 3 algorithms

**Swarm layer (`src/swarm/`):**
- `AgentPool.ts` ← agent lifecycle + auto-scaling
- `TopologyManager.ts` ← hierarchical/mesh/centralized/hybrid topologies
- `ConsensusEngine.ts` ← shared with orchestrator

**Agent layer (`src/agent/`):**
- `RAGMemoryAdapter.ts` ← semantic search + RVF learning store

**Security layer (`src/security/`):**
- `SecurityModule.ts` ← CVE fixes: path traversal, command injection, password hashing

**meow already does better than ruflo (keep, don't port):**
- MEOW-3-RULE self-healing (ruflo has nothing comparable)
- ExecutionMode multi-mode (SHIP/AUDIT_ONLY/PARALLEL)
- Mission Reviewer 7-dimension quality gates
- Daemon-style `meow -p` background dispatch
- EvolveHarness meta-loop

**Integration order recommendation:**
1. `ConsensusEngine` — multi-agent decision (Raft leader election for SHIP mode)
2. `TopologyManager` — O(1) role-based lookup for specialist/orchestrator queries
3. `SecurityModule` — always-on protection, no integration needed (static utility)
4. `RAGMemoryAdapter` — attach to existing AgenticMemory, enhance with semantic search
5. `EventStore` + `Hooks` — both integrate into Orchestrator via constructor injection
6. `Resilience` — wrap LLM API calls on-demand
7. `AgentPool` — requires SwarmManager refactor, do last

## Output Format

After comparison study, deliver:

```markdown
## [Reference] vs [Target] — Gap Analysis

### Reference Core Mechanisms
[Key innovations, ranked by importance]

### Target Already Does Well (keep)
[Where target is equal or superior — don't need to port]

### Target Gaps Worth Filling (port these)
| Feature | Reference approach | Priority | Difficulty | Action |
|---------|-------------------|----------|-----------|--------|
| Event Store | ADR-007 append-only log | P1 | Medium | Write src/orchestrator/EventStore.ts |
| Hooks | 17 hook points | P1 | Low | Write src/orchestrator/Hooks.ts |
| ... | ... | ... | ... | ... |

### Recommended Integration Order
1. EventStore → fastest value, audit trail
2. Hooks → medium effort, extensible
3. Resilience → on-demand use
4. AgentPool → most complex, do last
```

## Key Reminder: Direct Execution > Subagent for Codebase Exploration

**`delegate_task` reliably fails (HTTP 404) on heavy file operations.** Cloning large repos and extensive filesystem traversal via subagent consistently error out. **Do all filesystem work directly in the controller session:**
- `terminal()` — cloning, finding files, grep pipelines, diff
- `read_file()` — key source files
- `write_file()` — creating ported code in target repo

Use `delegate_task` only as the very last step — when you already know **exactly** what to write and just need a hand typing the code.

## Important: TypeScript LSP Noise Is Not Real Errors

When writing TypeScript files via `write_file` into a repo that has its own `tsconfig.json` and `node_modules/@types`, the LSP in the host environment will flag **false positives**:
- `Cannot find name 'events'` — `@types/node` not installed in host
- `Cannot find name 'setTimeout'` / `setInterval'` / `fs'` / `path'` — same reason
- `Property 'emit' does not exist` — `EventEmitter` from `events` not resolved

These are **environment issues**, not code errors. The files are valid TypeScript and will compile inside the target repo's own build. Do not waste time chasing these — just write the file and move on.

## Pro Tip: Study Reference Architecture via CLAUDE.md

Many well-engineered reference repos (like ruflo v3) have a comprehensive `CLAUDE.md` that encodes:
- Architecture patterns and design philosophy
- Anti-drift configurations
- Swarm orchestration protocols
- Auto-learning workflows

Read it early — it distills the codebase's conventions faster than reading 200 source files.

## Remember

```
Clone both → explore structure → deep study reference → compare → evaluate gaps → port high-value features
Do filesystem work directly (no subagent for cloning/traversal)
Cite source in docstrings when porting
Deliver comparison table + recommended action per gap
```