# Dashboard design comparison

The published “PrescriptXAI Operations Dashboard” reference images were unavailable
in the project materials. The local [written design brief](prompts/final_solo_prompts.md)
guided this implementation. Direct comparison with the reference is pending.

| Element | Current implementation | Verification |
| --- | --- | --- |
| Desktop and phone layout | Bordered cards for conditions, risk, prescription and follow-up. Cards stack on narrow screens. | Rendered at 1,360 and 390 CSS pixels. |
| Typography and theme | Streamlit with a system font stack and monospace risk values. | Chromium checked visible focus and edit restoration in both themes. The tested preset measured 14.24:1 in light mode and 15.56:1 in dark mode. The measured buttons, selectors and expanders were at least 44 CSS pixels. Full contrast coverage remains pending. |
| Risk and advisory status | Predicted risk from the fitted model, with text for the risk band and a permanent limits-status chip. The linked captures predate demonstration mode. | The case study renders at 87.7% for FD001 unit 82, cycle 156. |
| Advanced views | Fleet, Diagnostics, Evaluation and About remain accessible under Advanced. | Covered by the simulator integration tests. |

[Desktop capture](screenshots/phase17-simulator-desktop.png) ·
[Phone capture](screenshots/phase17-simulator-phone.png) ·
[Dark desktop](screenshots/phase17-simulator-desktop-dark.png) ·
[Dark phone](screenshots/phase17-simulator-phone-dark.png) ·
[Acceptance status](acceptance_report.md)
