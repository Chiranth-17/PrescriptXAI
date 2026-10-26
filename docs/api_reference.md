# Python and HTTP reference

These signatures and descriptions are generated from the installed-source docstrings at
documentation build time. Shared result schemas remain **2.0.0**; the package is **0.2.0**.
See [the decision pipeline guide](decision_pipeline.md) for request examples and input units.

## Public library

::: prescriptxai.pipeline.PrescriptXAI

## Shared input and result schemas

::: prescriptxai.schemas.InputContext

::: prescriptxai.schemas.Assessment

::: prescriptxai.schemas.RecourseResult

::: prescriptxai.schemas.ValidationReport

## HTTP application

Run `prescriptxai serve --config configs/default.yaml`. The live service exposes OpenAPI at
`/openapi.json` and interactive documentation at `/docs`. Health/readiness depends on fitted
artifact availability; a reachable web process alone does not establish model readiness.

::: prescriptxai.api.create_app

## Portable workspaces and reproduction

::: prescriptxai.workspace.initialize_workspace

::: prescriptxai.workspace.launch_dashboard

::: prescriptxai.reproduce.reproduce
