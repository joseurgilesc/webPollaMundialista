# puntajes-desglose — Specification

## Purpose

Provide a structured per-round breakdown of HOW points were earned, so the frontend can render human-readable scoring details inside the participant detail modal. The desglose is computed from existing raw `detalle` data already produced by `calificar.py` — no new scoring logic is introduced.

## Requirements

### Requirement: Backend emits `desglose` per round

Each participant result in `puntajes.json` MUST include a `desglose` field as a sibling of the existing `puntajes` and `detalle` fields. The `desglose` field MUST be a dict keyed by round name (`"16avos"`, `"8avos"`, `"cuartos"`, `"semifinales"`, `"finales"`). Each round entry SHALL contain an `items` array and a `subtotal` integer.

The `subtotal` MUST equal the corresponding `puntajes` value for that round.

#### Round type: 16avos — team hits + position hits

The `desglose` for `"16avos"` SHALL contain two groups in `items`:

- `{ "label": "Aciertos de equipo", "puntos": N, "count": N, "detalle": "N (+1 c/u)" }`
- `{ "label": "Aciertos de posición", "puntos": M, "count": M, "detalle": "M (+1 c/u)" }`

Where `count` is the number of items in `detalle["16avos"]["aciertos_equipo"]` and `detalle["16avos"]["aciertos_posicion"]` respectively. Each hit is worth 1 point.

#### Round type: Simple (8avos, cuartos, semifinales) — flat hits

The `desglose` for simple rounds SHALL contain a single group in `items`:

- `{ "label": "Aciertos", "puntos": N, "count": N, "detalle": "N (×2 pts) | N (×3 pts) | N (×4 pts)" }`

Where `count` is the number of items in `detalle["{round}"]["aciertos"]`, and points-per-hit varies by round: 2 for 8avos, 3 for cuartos, 4 for semifinales.

#### Round type: Finales — per-position hits

The `desglose` for `"finales"` SHALL contain one `items` entry per position, in order (Campeón, Segundo, Tercero, Cuarto):

- `{ "label": "Campeón", "puntos": 20|0, "equipo": "Equipo", "hit": true|false }`
- `{ "label": "Segundo", "puntos": 11|0, "equipo": "Equipo", "hit": true|false }`
- `{ "label": "Tercero", "puntos": 8|0, "equipo": "Equipo", "hit": true|false }`
- `{ "label": "Cuarto", "puntos": 5|0, "equipo": "Equipo", "hit": true|false }`

#### Scenario: 16avos with mixed hits and misses

- GIVEN a participant with 6 equipo hits and 5 posición hits in 16avos
- WHEN `calificar_polla()` computes the result
- THEN `desglose["16avos"]` SHALL contain `items: [{label:"Aciertos de equipo", puntos:6, count:6, detalle:"6 (+1 c/u)"}, {label:"Aciertos de posición", puntos:5, count:5, detalle:"5 (+1 c/u)"}]`
- AND `subtotal` SHALL be 11

#### Scenario: Simple round with all zero hits

- GIVEN a participant with 0 aciertos in 8avos
- WHEN `calificar_polla()` computes the result
- THEN `desglose["8avos"]` SHALL contain `items: [{label:"Aciertos", puntos:0, count:0, detalle:"0 (×2 pts)"}]`
- AND `subtotal` SHALL be 0

#### Scenario: Finales with mixed results

- GIVEN a participant who correctly predicted Campeón (Argentina) and Segundo (Brasil), but missed Tercero and Cuarto
- WHEN `calificar_polla()` computes the result
- THEN `desglose["finales"]` SHALL contain:
  - `{label:"Campeón", puntos:20, equipo:"ARGENTINA", hit:true}`
  - `{label:"Segundo", puntos:11, equipo:"BRASIL", hit:true}`
  - `{label:"Tercero", puntos:0, equipo:"ALEMANIA", hit:false}`
  - `{label:"Cuarto", puntos:0, equipo:"URUGUAY", hit:false}`
- AND `subtotal` SHALL be 31

#### Scenario: Simple round with mixed hits

- GIVEN a participant with 3 aciertos out of 8 predictions in cuartos
- WHEN `calificar_polla()` computes the result
- THEN `desglose["cuartos"]` SHALL contain `items: [{label:"Aciertos", puntos:9, count:3, detalle:"3 (×3 pts)"}]`
- AND `subtotal` SHALL be 9

#### Scenario: Empty round (no results yet)

- GIVEN a polla file exists but real results for that round are empty
- WHEN `calificar_polla()` computes the result
- THEN `desglose["{round}"]` SHALL contain `items: [{label:"Aciertos", puntos:0, count:0, detalle:"0 (×N pts)"}]`
- AND `subtotal` SHALL be 0

---

### Requirement: Frontend renders desglose in participant modal

The modal at `docs/index.html` SHALL render a `desglose` section for each round AFTER the existing score bars and BEFORE the bracket table. The desglose section SHALL use Spanish labels with an azul (blue) / rojo (red) color scheme on white background.

#### Desglose container structure

The desglose section for each round SHALL be a `div` with white background, containing:
- A round header (e.g., "16avos · 11 pts")
- A list of desglose items

#### Color scheme

- Items where `puntos > 0` SHALL render in blue (`color: #1a6fb5` or similar azul)
- Items where `puntos === 0` SHALL render in muted red (`color: #dc2626` or similar rojo) to indicate misses
- The background SHALL be white (`#ffffff`)

#### Round type: 16avos display

The desglose for 16avos SHALL render two lines:
- `✓ Aciertos de equipo: 6 (+1 c/u) = 6 pts` (in blue)
- `✓ Aciertos de posición: 5 (+1 c/u) = 5 pts` (in blue)

If either count is 0, the line SHALL still render but in muted red:
- `✗ Aciertos de equipo: 0 (0 pts)` (in red)

#### Round type: Simple display (8avos, cuartos, semifinales)

The desglose for simple rounds SHALL render one line with the hit count and multiplier:
- `✓ Aciertos: 3 (×3 pts) = 9 pts` (in blue if count > 0)
- `✗ Aciertos: 0 (×4 pts) = 0 pts` (in red if count === 0)

#### Round type: Finales display

The desglose for finales SHALL render one line per position:
- `✓ Campeón: Argentina (+20 pts)` (blue)
- `✗ Segundo: Brasil (0 pts)` (red if miss)
- `✗ Tercero: Alemania (0 pts)` (red if miss)
- `✓ Cuarto: Uruguay (+5 pts)` (blue)

Each line SHALL include the team name as displayed text.

#### Scenario: Modal renders with mixed scores

- GIVEN a participant with 11 pts in 16avos (6 equipo + 5 posición), 9 pts in cuartos (3 aciertos × 3), and 31 pts in finales (Campeón + Segundo)
- WHEN `verPolla()` renders the modal
- THEN the desglose section SHALL show blue lines for hits and red for zero-count items
- AND the bracket table SHALL appear below the desglose section

#### Scenario: Modal renders with zero scores across all rounds

- GIVEN a participant with 0 pts in every round
- WHEN `verPolla()` renders the modal
- THEN every desglose line SHALL render in red with `0 pts`
- AND the modal SHALL NOT throw JavaScript errors
- AND the modal SHALL render normally without visual breakage

---

### Requirement: Frontend receives desglose data

The `PUNTAJES` JavaScript constant in `docs/index.html` MUST include the full `desglose` field per participant. The `generar_sitio.py` script SHALL NOT strip the `detalle` field (or its computed `desglose` counterpart) from the embedded JSON data.

#### Scenario: desglose included in PUNTAJES

- GIVEN `calificar.py` has produced `puntajes.json` with `desglose` data
- WHEN `generar_sitio.py` generates `docs/index.html`
- THEN `PUNTAJES` in the embedded `<script>` SHALL include a `desglose` key for each participant
- AND accessing `PUNTAJES[i].desglose` SHALL return the structured breakdown

---

### Requirement: Edge case — missing desglose for a round

If a round's `detalle` data is absent, empty, or malformed, the backend SHALL produce a safe fallback `desglose` entry with `items: [{label:"Aciertos", puntos:0, count:0, detalle:"Sin datos"}]` and `subtotal: 0`.

The frontend SHALL handle missing `desglose` gracefully: if `PUNTAJES[i].desglose` is undefined or null, the desglose section SHALL NOT render, but the rest of the modal SHALL work normally.

#### Scenario: Missing round data in backend

- GIVEN a polla has no `ronda_semifinales` key
- WHEN `calificar_polla()` computes results
- THEN `desglose["semifinales"]` SHALL be `{items: [{label:"Aciertos", puntos:0, count:0, detalle:"Sin datos"}], subtotal: 0}`

#### Scenario: Missing desglose in frontend (backward compatibility)

- GIVEN an older `puntajes.json` without `desglose` fields
- WHEN `verPolla()` renders a participant's modal
- THEN the modal SHALL render score bars and bracket table as before
- AND NO desglose section SHALL appear
- AND NO JavaScript error SHALL be thrown

---

## Non-Goals

- The desglose MUST NOT introduce new scoring logic — it is derived from existing `detalle` data
- The desglose MUST NOT modify the `puntajes` totals
- No changes to `docs/admin.html` or the admin experience
- No changes to the chart, leaderboard table, or share functionality
- No reactive data or JavaScript frameworks
- No collapsible/toggle behavior for desglose sections (though not prohibited)
