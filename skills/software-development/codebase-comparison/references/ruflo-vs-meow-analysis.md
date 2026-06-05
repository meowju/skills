# ruflo v3 → meow Gap Analysis

**Date:** 2026-01-20
**Reference:** ruvnet/ruflo (53,420 stars, v3/@claude-flow/)
**Target:** stancsz/meow

---

## ruflo v3 Architecture

```
ruflo/
  v3/
    @claude-flow/
      swarm/           # Queen-led hierarchical mesh, 15 agent types
        src/
          queen-coordinator.ts    # agent orchestration
          agent-pool.ts           # lifecycle + auto-scaling
          topology-manager.ts     # role-based O(1) lookup
          consensus/
            raft.ts              # leader election + log replication
            byzantine.ts         # Byzantine fault tolerance
            gossip.ts            # epidemic state propagation
      memory/          # HybridBackend (SQLite + AgentDB + HNSW)
        src/
          hybrid-backend.ts      # 150x-12500x faster vector search
          persistent-sona.ts     # self-learning coordinator
          rvf-learning-store.ts   # pattern learning + persistence
      shared/src/
        hooks/index.ts           # 17 lifecycle hook points
        resilience/index.ts      # Retry + CB + Bulkhead + RateLimiter
        plugin-registry.ts       # ADR-004 microkernel architecture
        mcp/index.ts             # MCP bridge (JSON-RPC 2.0)
      guidance/src/              # CLAUDE.md compilation + shard retrieval
      browser/
        src/
          domain/signed-trajectory.ts  # Ed25519 witness signing
      security/                  # CVE fixes (path traversal, command injection)
```

---

## What meow Does Better (keep, don't port)

| Feature | meow | ruflo |
|---------|------|-------|
| Self-repair | MEOW-3-RULE: `claude -p` fixes own code after 3 failures | None |
| Execution modes | SEQUENTIAL/PARALLEL/SHIP/AUDIT_ONLY | Single hierarchical |
| Quality gates | 7-dimension Mission Reviewer (NO_MOCKS/TYPE_CHECK/LINT_CLEAN/SOP_COMPLIANCE) | None |
| CLI style | Daemon `meow -p` background + foreground return | Synchronous CLI |
| Meta-learning | EvolveHarness: LLM-level self-evolution loop | None |
| Agent layers | L1→L4 explicit separation (liaison→architect→orchestrator→specialists) | Flat swarm |

---

## Ported Files Summary

| File | Source | Purpose |
|------|--------|---------|
| `src/orchestrator/EventStore.ts` | ruflo ADR-007 | Append-only event log, full audit trail |
| `src/orchestrator/Hooks.ts` | ruflo shared/hooks | 17 lifecycle hook points |
| `src/orchestrator/Resilience.ts` | ruflo shared/resilience | Retry + CircuitBreaker + Bulkhead |
| `src/swarm/ConsensusEngine.ts` | ruflo swarm/consensus/ | Raft + Byzantine + Gossip |
| `src/swarm/TopologyManager.ts` | ruflo swarm/topology-manager.ts | O(1) role lookup |
| `src/swarm/AgentPool.ts` | ruflo swarm/agent-pool.ts | Agent lifecycle + auto-scaling |
| `src/agent/RAGMemoryAdapter.ts` | ruflo memory/ | Semantic RAG + RVF learning |
| `src/mcp/MCPBridge.ts` | ruflo shared/mcp/ | JSON-RPC 2.0 + transports |
| `src/guidance/GuidanceControlPlane.ts` | ruflo guidance/ | CLAUDE.md compile + shards |
| `src/security/SecurityModule.ts` | ruflo security/ | CVE: path traversal, command injection |
| `src/browser/SignedTrajectory.ts` | ruflo browser/witness-signer.ts | Ed25519 signing |
| `src/plugins/PluginManager.ts` | ruflo shared/plugin-registry.ts | Microkernel plugin system |

---

## Integration: Orchestrator.ts

**Constructor:** adds `eventStore`, `hooks`, `guidance` + `registerOrchestratorHooks()`
**execute():** emits `mission:started/completed` events + `emit()` via EventEmitter
**New methods:** `registerOrchestratorHooks()`, `getEventStore()`, `getHooks()`, `getGuidance()`

## Integration: agent.ts

**New fields:** `ragMemory`, `mcpBridge`, `hooks`, `llmCircuitBreaker`
**Constructor:** initializes all four enhanced components