---
phase: 9
plan: 3
wave: 3
depends_on: [9.2]
autonomous: true
---

# Profile, optimize and measure bounded memory

1. Commit a fixture-only performance protocol/helper before its baseline: actual fitted model,
   fixed states/engines/repeats/seeds, cold/warm scope and all-sample retention. Profile cProfile
   and save actual source/config/runtime hashes. This is a development microbenchmark, not a
   replacement for any Phase7 historical measurement or deployment-wide target.
2. Optimize a measured hot path without changing scientific results. Require unchanged golden
   outputs and identical measured populations/settings; report before/after latency with whole-
   engine bootstrap intervals/counts. Keep outliers and disclose process segments.
3. Check Python allocation and process-memory growth over10000 complete public calls with a
   declared warmup/baseline and retained checkpoints; document allocator/platform limitations.

Done: profile, result parity, actual before/after samples and10000-call memory evidence exist.
