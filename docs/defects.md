# Defect log

Every entry names the symptom, root cause, fix and regression evidence. Historical Phase 7
measurements remain unchanged; fixes below apply to later software revisions.

| ID | Symptom | Root cause | Fix | Regression test | Status |
|---|---|---|---|---|---|
| P8-001 | Manual preview could accept a candidate without its required learned coupling model | Preview omitted the optimizer's required-coupling guard | Fail closed with typed ArtifactError; API returns structured 503 | test_missing_required_coupling_fails_closed | Fixed |
| P8-002 | Malformed direct-library modes could raise TypeError or ambiguous truth errors | Truthiness and hash membership preceded string validation | Explicit None default and string validation | test_library_modes_reject_malformed_types | Fixed |
| P8-003 | Huge integers or finite extreme controls could escape typed input errors | Float conversion omitted OverflowError; scaled representability unchecked | Catch conversion overflow and reject values unrepresentable by supported float32 predictors; physical bounds unchanged | test_manual_preview_rejects_bad_measurements | Fixed |
