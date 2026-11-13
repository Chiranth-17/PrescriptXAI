"""Local-only presentation tokens for the operator workspace."""

STYLE = """
<style>
.stApp {
  --psx-bg: #f2f5fa; --psx-panel: #ffffff; --psx-ink: #172b46;
  --psx-muted: #52657b; --psx-line: #dde5f0; --psx-blue: #1d4ed8;
  --psx-soft: #edf3ff; --psx-teal: #086779; --psx-teal-soft: #e9f7f5;
  --psx-focus: #1d4ed8; --psx-shadow: 0 6px 24px rgb(27 52 91 / 5%);
  background: radial-gradient(ellipse at 10% 0%, #e4edff 0, transparent 40%), var(--psx-bg);
  color: var(--psx-ink);
  font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: 1440px; padding: 2.4rem 3rem 5rem; }
[data-testid="stAppDeployButton"] { display: none; }
.stApp h1, .stApp h2, .stApp h3 { color: var(--psx-ink); letter-spacing: -0.035em; }
.stApp h3 { font-size: 1.35rem; font-weight: 750; padding-top: 0; }
.stApp p, .stApp label { color: var(--psx-ink); }
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] * { color: var(--psx-muted); line-height: 1.65; }
.st-key-psx-hero { position: relative; padding: .35rem 0 1rem 5rem; }
.st-key-psx-hero::before {
  content: "P"; position: absolute; left: 0; top: .8rem;
  display: grid; place-items: center; width: 58px; height: 58px;
  color: white; background: linear-gradient(135deg, #2459e5, #1439ad);
  border-radius: 17px; font: 750 30px "Segoe UI", sans-serif;
  box-shadow: 0 8px 20px rgb(29 78 216 / 22%);
}
.st-key-psx-hero h1 { font-size: clamp(1.8rem, 3vw, 2.7rem); padding: 0; line-height: 1.18; }
.st-key-psx-kicker [data-testid="stCaptionContainer"] * {
  color: var(--psx-blue); font-size: .7rem; font-weight: 750; letter-spacing: .14em;
}
.st-key-psx-machine, .st-key-psx-context, .st-key-psx-controls,
.st-key-psx-risk, .st-key-psx-prescription, .st-key-psx-followup {
  background: var(--psx-panel); border: 1px solid var(--psx-line) !important;
  border-radius: 20px; box-shadow: var(--psx-shadow); padding: 1.4rem !important;
}
.st-key-psx-machine { padding: .8rem 1.2rem !important; }
.st-key-psx-identity { gap: .35rem; }
.st-key-psx-identity [data-testid="stCaptionContainer"] p { font-size: .8rem; }
.st-key-psx-scenarios { padding: .35rem 0 .65rem; }
.st-key-psx-scenarios button { border-radius: 999px !important; padding: .6rem 1rem; }
.stApp .stButton button, .stApp .stDownloadButton button {
  min-height: 44px; border: 1px solid var(--psx-line); border-radius: 11px;
  background: var(--psx-panel); color: var(--psx-ink); font-weight: 650;
  transition: border-color 120ms ease, box-shadow 120ms ease;
}
.stApp .stButton button:hover, .stApp .stDownloadButton button:hover {
  border-color: var(--psx-blue); color: var(--psx-blue);
  box-shadow: 0 3px 12px rgb(29 78 216 / 9%);
}
.stApp .stButton button[kind="primary"] {
  background: var(--psx-blue); color: #fff; border-color: var(--psx-blue);
  box-shadow: 0 4px 12px rgb(29 78 216 / 14%);
}
.stApp .stButton button[kind="primary"] p { color: #fff; }
.stApp button:disabled { opacity: .55; box-shadow: none; }
.stApp .stButton button[kind="primary"]:hover { background: #173fae; color: white; }
.st-key-psx-context h3::before, .st-key-psx-risk h3::before,
.st-key-psx-prescription h3::before, .st-key-psx-followup h3::before {
  content: ""; display: inline-block; width: 5px; height: 1.15em;
  vertical-align: -.16em; border-radius: 8px; background: var(--psx-blue); margin-right: .65rem;
}
.stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div {
  background: var(--psx-bg); border: 1px solid var(--psx-line); border-radius: 10px;
  min-height: 44px; color: var(--psx-ink);
}
.stApp [data-testid="stSelectbox"] [role="combobox"] { min-height: 44px; }
.stApp [data-testid="stSlider"] { padding: .4rem .1rem .65rem; min-height: 64px; }
.stApp [data-testid="stSlider"] label p { font-size: .84rem; font-weight: 650; }
.stApp [data-testid="stSliderTickBarMin"], .stApp [data-testid="stSliderTickBarMax"] {
  color: var(--psx-muted); font-size: .7rem;
}
.stApp [data-testid="stMetricLabel"] p { font-size: .82rem;
  font-weight: 600;
  color: var(--psx-muted);
  }
.stApp [data-testid="stMetricValue"] {
  font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
  font-weight: 700; letter-spacing: -.06em; color: var(--psx-ink);
}
.stApp [data-testid="stMetricValue"] * { color: inherit; }
.st-key-psx-risk { border-top: 4px solid var(--psx-blue) !important;
  background: linear-gradient(125deg, var(--psx-panel), var(--psx-soft));
  }
.st-key-psx-risk [data-testid="stMetricValue"] { font-size: 3.7rem; line-height: 1.15; }
.st-key-psx-prescription [data-testid="stMetricValue"] { font-size: 3rem; color: var(--psx-blue); }
.st-key-psx-prescription [data-testid="stMetricValue"] * { color: var(--psx-blue); }
.psx-risk-meter { height: 8px;
  background: var(--psx-line);
  border-radius: 20px;
  overflow: hidden;
  margin: .25rem 0 .1rem;
  }
.psx-risk-meter > span { display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--psx-blue);
  }
.psx-risk-meter[data-band="Alert"] > span { background: #b15b12; }
.psx-risk-meter[data-band="Low"] > span { background: var(--psx-teal); }
.stApp [class*="st-key-psx-action-"] {
  background: var(--psx-soft); padding: 1rem; border-radius: 13px;
  border: 1px solid var(--psx-line); box-shadow: none;
}
.stApp [class*="st-key-psx-action-"] [data-testid="stMarkdownContainer"] p { font-weight: 650;
  font-size: .9rem;
  }
.stApp [class*="st-key-psx-action-"] [data-testid="stCaptionContainer"] p { font-size: .79rem; }
.stApp [class*="st-key-psx-check-"] { position: relative;
  padding: .75rem 1rem .75rem 2.7rem;
  border-radius: 10px;
  }
.stApp [class*="st-key-psx-check-"][class*="-pass"] { background: var(--psx-teal-soft); }
.stApp [class*="st-key-psx-check-"][class*="-fail"] { background: #fff0e8; }
.stApp [class*="st-key-psx-check-"]::before {
  content: "✓"; position: absolute; left: .85rem; top: .75rem;
  color: var(--psx-teal); font-weight: 800;
}
.stApp [class*="st-key-psx-check-"][class*="-fail"]::before { content: "!"; color: #a8310f; }
.stApp [class*="st-key-psx-check-"] p { font-size: .88rem; font-weight: 650; }
.st-key-psx-followup { margin-top: .5rem; }
.st-key-psx-followup [data-testid="stMetricValue"] { font-size: 2.2rem; }
.stApp [data-testid="stExpander"] { border: 1px solid var(--psx-line);
  border-radius: 11px;
  background: var(--psx-panel);
  }
.stApp .stExpander summary { min-height: 44px; color: var(--psx-ink); }
.stApp :is(button, [role="combobox"], summary):focus-visible,
.stApp [data-testid="stSlider"]:has(input[type="range"]:focus-visible) {
  outline: 3px solid var(--psx-focus); outline-offset: 3px;
}
@media (prefers-color-scheme: dark) {
  .stApp { --psx-bg: #0c1526; --psx-panel: #152238; --psx-ink: #edf3fc;
    --psx-muted: #b0c1d7; --psx-line: #32445e; --psx-blue: #a4c1ff;
    --psx-soft: #1b2d4d; --psx-teal: #9de4df; --psx-teal-soft: #123b43;
    --psx-focus: #a4c1ff; background: var(--psx-bg); }
  .stApp .stButton button[kind="primary"] { background: #234dbd;
  border-color: #829ee6;
  color: white;
  }
  .stApp [class*="st-key-psx-check-"][class*="-fail"] { background: #4b2921; }
  .stApp [class*="st-key-psx-check-"][class*="-fail"]::before { color: #ffc5a8; }
}
@media (max-width: 600px) {
  [data-testid="stMainBlockContainer"] { padding: 1.5rem 1rem 3rem; }
  .st-key-psx-hero { padding-left: 3.7rem; }
  .st-key-psx-hero::before { width: 43px; height: 43px; border-radius: 13px; font-size: 23px; }
  .st-key-psx-hero h1 { font-size: 1.75rem; }
  .st-key-psx-controls, .st-key-psx-context, .st-key-psx-risk,
  .st-key-psx-prescription, .st-key-psx-followup { padding: 1.1rem !important;
  border-radius: 16px;
  }
  [data-testid="stHorizontalBlock"] { flex-direction: column; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { width: 100%; min-width: 0; }
  .st-key-psx-scenarios, .st-key-psx-scenarios [data-testid="stHorizontalBlock"] {
  flex-direction: row;
  flex-wrap: wrap;
  gap: .5rem;
  }
  .st-key-psx-scenarios button { font-size: .8rem; }
}
@media (prefers-reduced-motion: reduce) { .stApp button { transition: none; } }
</style>
<span data-psx-theme="operator-workspace" hidden aria-hidden="true"></span>
"""
