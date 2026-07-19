# Proposal: FIFA-Compliant Group Sorting + Stats Table Redesign

## Intent

Group standings computed by the pool system must match FIFA Article 13 tiebreaker criteria (PTS > GD > GF > H2H pts > H2H GD > H2H GF > fair play / drawing of lots). Previously, the system relied on the API's raw ordering or ad-hoc processing, which produced incorrect rankings in edge cases (e.g., Grupo B with all 4 teams tied at 4 pts / 0 GD / 1 GF). Concurrently, team stats displayed as inline text ("3pts 2-1 +1") were hard to scan; a proper HTML table with aligned columns is needed.

## Scope

### In Scope
- Implement `_h2h_scores()`, `_fifa_sort_key()`, `_sort_group()` in `scripts/fetch_resultados.py` that replicates FIFA Article 13 tiebreakers in exact order
- Use the same engine for best third-placed team selection (reads from `grupos_result`, not raw API)
- Replace inline stats display with `<table class="stats-table">` showing `# | Eq | PTS | GF | GA | GD` columns in both Python template and JS rendering
- Keep interactive manual tiebreak fallback (console `input()` with FIFA.com link) for unresolvable ties

### Out of Scope
- Automating fair play / drawing of lots tiebreaks (out of our control — FIFA decides)
- Writing automated unit tests (project has no test runner per `config.yaml`)
- Adding the stats table outside the participant modal (e.g., public leaderboard)

## Capabilities

### New Capabilities
- None — this change modifies existing behavior at the implementation level only.

### Modified Capabilities
- None — no spec files exist in `openspec/specs/` yet. Pure implementation + visual redesign.

## Approach

Already implemented. Code changes:
1. **`scripts/fetch_resultados.py`** — Added `_h2h_scores()` (head-to-head calculator), `_fifa_sort_key()` (sorting tuple), `_sort_group()` (full FIFA Article 13 sort with groupby-based H2H resolution and interactive manual fallback). Best third-placed selection reads from `grupos_result` which already has final FIFA ordering.
2. **`scripts/generar_sitio.py` + `docs/index.html`** — Replaced inline stats string with `<table class="stats-table">` inside the modal group view. Columns: `# | Eq | PTS | GF | GA | GD`. Both the Python `generar_publica()` template and the JS `verPolla()` function updated.

Pending: verification pipeline — run the full pipeline when the API returns data, and manually verify Grupo B (4 teams tied at 1pt/0GD/1GF → should trigger tiebreak prompt) and Grupo C (Brazil/Morocco tied).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `scripts/fetch_resultados.py` | Modified | Added `_h2h_scores()`, `_fifa_sort_key()`, `_sort_group()` — FIFA-compliant group sort engine |
| `scripts/generar_sitio.py` | Modified | Updated `verPolla()` template to emit `<table class="stats-table">` with PTS/GF/GA/GD |
| `docs/index.html` | Modified | Inline CSS for `.stats-table` added within `<style>`. JS `verPolla()` renders the new table |
| `data/resultados_reales.json` | Data | `_stats` key already populated by the engine for frontend use |
| `scripts/calificar.py` | None | Scoring unchanged — reads from `resultados_reales.json` regardless of sort |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| API worldcup26.ir down at verification time | High | Manual data entry in `resultados_reales.json` with `--manual` flag |
| Grupo B 4-way tie triggers false positive | Low | Manual tiebreak prompt is interactive — operator must decide, engine doesn't guess |
| Stats table breaks existing modals | Low | Old and new JS paths are the same (`verPolla`) — table replaces inline text with identical data |

## Rollback Plan

Revert the two files to their previous commits: `git checkout HEAD~1 -- scripts/fetch_resultados.py scripts/generar_sitio.py docs/index.html`. Then regenerate: `python3 scripts/generar_sitio.py`.

## Dependencies

- `worldcup26.ir` API being online for full pipeline verification
- Manual input for Grupo B tiebreaker (cannot be automated)

## Success Criteria

- [ ] `scripts/fetch_resultados.py` runs without errors when `worldcup26.ir` returns standings
- [ ] Running with existing `resultados_reales.json` produces correct sorted groups (Grupo A: Mexico 1st, Korea 2nd; Grupo D: USA 1st, Australia 2nd)
- [ ] Grupo B with 4-way tie triggers interactive manual tiebreak prompt with accurate stats display
- [ ] Grupo C with Brazil/Morocco tied resolves via H2H correctly
- [ ] Stats table in modal shows `# | Eq | PTS | GF | GA | GD` as aligned columns for every group
