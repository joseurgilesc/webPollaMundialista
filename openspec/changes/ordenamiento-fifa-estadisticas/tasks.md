# Tasks: FIFA-Compliant Group Sorting + Stats Table Redesign

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~0 (all implementation already done) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | FIFA sort engine | PR 1 | Already implemented in `fetch_resultados.py`. No code changes. |
| 2 | Stats table redesign | PR 1 | Already implemented in `generar_sitio.py` + `docs/index.html`. No code changes. |
| 3 | Pipeline verification | PR 1 | Pending verification run — depends on API availability. |

## Phase 1: FIFA Group Sort Engine (Already Done)

- [x] 1.1 Add `_h2h_scores()` to `scripts/fetch_resultados.py` — head-to-head calculator for tied teams
- [x] 1.2 Add `_fifa_sort_key()` to `scripts/fetch_resultados.py` — descending sort key (PTS, GD, GF)
- [x] 1.3 Add `_sort_group()` to `scripts/fetch_resultados.py` — full FIFA Article 13 multi-pass sort with `groupby` tie bundles
- [x] 1.4 Add interactive console tiebreak fallback with input validation in `_sort_group()`
- [x] 1.5 Wire `_sort_group()` into group processing loop — best third-placed reads from sorted `grupos_result`
- [x] 1.6 Serialize `_stats` dict with PTS/GF/GA per team per group into `resultados_reales.json`

## Phase 2: Stats Table Redesign (Already Done)

- [x] 2.1 Add `.stats-table` CSS rules (`.modal-grupo .stats-table`, `th`, `td`) to `generar_sitio.py` template
- [x] 2.2 Replace inline stats `<div>` with `<table class="stats-table">` in Python `generar_publica()` template — columns `# | Eq | PTS | GF | GA | GD`
- [x] 2.3 Replace inline stats in JS `verPolla()` rendering (in `generar_sitio.py` template) — same table structure
- [x] 2.4 Add GD sign prefix logic (`+3`, `0`, `-1`) in both Python and JS renderers
- [x] 2.5 Add empty-cell fallback when `_stats` entry is missing
- [x] 2.6 Regenerate `docs/index.html` via `generar_sitio.py`

## Phase 3: Verification (Pending — API-dependent)

- [ ] 3.1 Run full pipeline: `python3 scripts/fetch_resultados.py` → `python3 scripts/calificar.py` → `python3 scripts/generar_sitio.py`
- [ ] 3.2 Verify Grupo A: Mexico 1st, Korea 2nd per FIFA Article 13
- [ ] 3.3 Verify Grupo D: USA 1st, Australia 2nd per FIFA Article 13
- [ ] 3.4 Verify Grupo B: 4-way tie triggers interactive tiebreak prompt with accurate stats
- [ ] 3.5 Verify Grupo C: Brazil/Morocco H2H tie resolves correctly
- [ ] 3.6 Open participant modal — confirm `<table class="stats-table">` renders with correct `# | Eq | PTS | GF | GA | GD` columns
- [ ] 3.7 Verify GD sign prefix rendering: `+3`, `0`, `-1` in modal
- [ ] 3.8 Verify unfinished groups show rank-0 with empty stats cells
- [ ] 3.9 If API is down: use `--manual` flag with `resultados_reales.json` to test offline
