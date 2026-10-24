# Defect log

Every entry names the symptom, root cause, fix and regression evidence. Historical Phase 7
measurements remain unchanged; fixes below apply to later software revisions.

| ID | Symptom | Root cause | Fix | Regression test | Status |
|---|---|---|---|---|---|
| P8-001 | Manual preview could accept a candidate without its required learned coupling model | Preview omitted the optimizer's required-coupling guard | Fail closed with typed ArtifactError; API returns structured 503 | test_missing_required_coupling_fails_closed | Fixed |
| P8-002 | Malformed direct-library modes could raise TypeError or ambiguous truth errors | Truthiness and hash membership preceded string validation | Explicit None default and string validation | test_library_modes_reject_malformed_types | Fixed |
| P8-003 | Huge integers or finite extreme controls could escape typed input errors | Float conversion omitted OverflowError; scaled representability unchecked | Catch conversion overflow and reject values unrepresentable by supported float32 predictors; physical bounds unchanged | test_manual_preview_rejects_bad_measurements | Fixed |
| P8-004 | Repeating an old edit after a selection/recompute could skip preview validation | Old control signature survived result invalidation | Clear signature with results and sliders | test_session_invalidates_results_and_widgets | Fixed |
| P8-005 | Changing a mapped artifact could retain a stale cached model | Resource key hashed default rather than selected artifact paths | Resolve the same model-artifact mapping before content hashing | test_direct_adapter_uses_real_fitted_artifacts | Fixed |
| P8-006 | Uploaded or replayed boolean sensors could become 1.0 | Premature numeric coercion | Preserve upload types and reject booleans at observed telemetry/history boundary | test_sources_and_settings_fail_explicitly; test_observed_state_excludes_labels_and_preserves_actual_prefix | Fixed |
| P8-007 | Setting dashboard config or API key prevented profile loading | All prefixed service environment variables were interpreted as scientific YAML fields | Reserve service settings/credentials, retaining strict scientific overrides | test_service_environment_variables_do_not_override_scientific_config | Fixed |
| P8-008 | Context engine/cycle metadata rejected models whose taxonomy omits those fields | Metadata was always merged into predictor telemetry | Merge IDs/cycles only when configured as telemetry; retain InputContext provenance | test_operator_selection_risk_solve_slider_and_exports | Fixed |
