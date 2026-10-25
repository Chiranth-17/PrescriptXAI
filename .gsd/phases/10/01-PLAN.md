---
phase: 10
plan: 1
depends_on: [phase9-closed]
autonomous: true
---

# Installable release and portable entrypoints

1. Correct wheel runtime dependencies/extras and packaged default configuration/dashboard assets;
   unify semantic version0.2.0, changelog, MIT (user delegated choice), CITATION and notices.
2. Build sdist/wheel; inspect their contents; install into an isolated clean environment and verify
   library/CLI/config initialization outside the checkout. Add meaningful package/resource tests.
3. Multi-stage non-root Docker image/compose with real healthchecks and data/artifact volumes.
   Docker server29.4.0 is available: build and run both services, record identity/health/UID proof.

Done: actual clean distribution installation and container checks pass, no bundled fitted data.
