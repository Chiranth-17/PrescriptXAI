# Dashboard design comparison

The user-supplied desktop and phone references are preserved byte for byte.
Their 2× captures represent widths of 1,360 and 390 CSS pixels. The mockups'
risk values, recommendations and feedback illustrate the design. The
live captures are from browser run v14 and show the registered FD001 replay.

| Element | Difference | Disposition |
| --- | --- | --- |
| Page structure | Both views have four numbered sections. The live desktop reserves a full-width area for recorded unit and cycle before the columns, and the phone stacks the cards. | Keep recorded context visible and preserve the single-column mobile flow. |
| Presets and settings | Mock presets use flight descriptions and show fixed-context sliders. Live presets identify recorded replay examples, fixed values are in an expander, and adjustable settings come from the machine spec. | Keep machine-scoped values and a clear boundary between recorded context and editable controls. |
| Risk and prescription | The mock uses an arrow, colored risk scale and colored check tiles. Live risk uses separate sections, with text for the risk band, validation results and the demonstration limits label. | Keep explicit status text. The live case renders 87.7% current predicted risk and 15.0% with the prescription. |
| Follow-up | The mock previews a single adherence slider, visible trend and populated log. The live page has per-setting inputs, an opt-in later replay and a collapsible log. | Keep the actual applied values and explicit provenance of any simulated records. |
| Advanced views | The mock focuses on the simulator. The live view also links to Fleet, Diagnostics, Evaluation and About. | Keep the existing analysis pages in Advanced. |

- [Desktop mockup](design/dashboard_mock_desktop.png) and [phone mockup](design/dashboard_mock_phone.png)
- [Live desktop](screenshots/phase17-demonstration-desktop.png) and [live phone](screenshots/phase17-demonstration-phone.png)
- [Earlier dark desktop](screenshots/phase17-simulator-desktop-dark.png) and [earlier dark phone](screenshots/phase17-simulator-phone-dark.png)
- [Acceptance status](acceptance_report.md) and [usability kit](usability_notes.md)
