# Tasks: desglose-puntos-modal

## Task List

### Task 1 — Add `_computar_desglose()` to calificar.py

**Description**: Implement `_computar_desglose(puntajes: dict, detalle: dict) -> dict` that reads existing `detalle` per round and returns structured `desglose` dict. Integrate into `calificar_polla()` by calling it after all scoring loops, right before returning `resultado`.

**Files affected**:
- `scripts/calificar.py` — add ~70 lines for the function + 2 lines for the call in `calificar_polla()`

**Details**:

The function must handle three round types:

1. **16avos**: From `detalle["16avos"]["aciertos_equipo"]` (list) and `detalle["16avos"]["aciertos_posicion"]` (list). Count each → 1 pt/item. Produces two items:
   - `{label:"Aciertos de equipo", puntos:N, count:N, detalle:"N (+1 c/u)"}`
   - `{label:"Aciertos de posición", puntos:M, count:M, detalle:"M (+1 c/u)"}`

2. **Simple rounds (8avos, cuartos, semifinales)**: From `detalle["{round}"]["aciertos"]` (list). Points per hit vary: 8avos=2, cuartos=3, semifinales=4. Produces one item:
   - `{label:"Aciertos", puntos:N, count:N, detalle:"N (×N pts)"}`

3. **Finales**: From `detalle["finales"]["aciertos"]` (list of strings like `"campeon: ARGENTINA (+20)"` for hits, `"segundo: predijo BRASIL, real: ALEMANIA (0 pts)"` for misses). Parse each string to extract position, team, hit/miss, and points. Produces up to 4 items (campeon, segundo, tercero, cuarto):
   - `{label:"Campeón", puntos:20|0, equipo:"ARGENTINA", hit:true|false}`
   - `{label:"Segundo", puntos:11|0, equipo:"BRASIL", hit:true|false}`
   - `{label:"Tercero", puntos:8|0, equipo:"ALEMANIA", hit:true|false}`
   - `{label:"Cuarto", puntos:5|0, equipo:"URUGUAY", hit:true|false}`

**Edge cases** (ref: spec scenario):
- Missing/empty detalle for a round → produce `{items:[{label:"Aciertos", puntos:0, count:0, detalle:"Sin datos"}], subtotal:0}`
- Missing finales detalle → produce all 4 positions with puntos:0 and equipo from the polla (if available) or "?"
- Empty finales detalle["aciertos"] → entries parsed from detalle["finales"]["errores"] (strings like `"campeon: predijo ARGENTINA, real:  (0 pts)"`)

**Parse logic for finales strings**:
- Hit pattern: `"{puesto}: {equipo} (+{pts})"` — grupo(1)=team, grupo(2)=pts
- Miss pattern: `"{puesto}: predijo {equipo}, real: {real} ({pts} pts)"` — grupo(1)=predicted team, grupo(2)=pts (always 0)
- Position labels to standardize: {"campeon":"Campeón","segundo":"Segundo","tercero":"Tercero","cuarto":"Cuarto"}

**Integration**: Add to `calificar_polla()` after the finales scoring block, right before `resultado["puntajes"]["total"] = total`:
```python
resultado["desglose"] = _computar_desglose(resultado["puntajes"], resultado["detalle"])
```

**Verification**:
- Run `python3 scripts/calificar.py` and confirm `data/puntajes.json` contains `desglose` field per participant
- Marcia Eguez: `desglose["16avos"]` → items[0].puntos=6, items[1].puntos=5, subtotal=11
- Carmen Carrasco: `desglose["16avos"]` → items[0].puntos=5, items[1].puntos=5, subtotal=10
- All `puntajes` totals remain unchanged (desglose subtotals must match corresponding `puntajes` values)
- Zero-score rounds have items[0].puntos=0

---

### Task 2 — Include `desglose` in PUNTAJES constant

**Description**: Modify `generar_sitio.py` line 901 to include `desglose` in the PUNTAJES JS constant. Currently it strips to only `participante`, `archivo`, and `puntajes`. It must also include `desglose`.

**Files affected**:
- `scripts/generar_sitio.py` — change line 901

**Details**:

Before (line 901):
```python
const PUNTAJES = {json.dumps([{"participante": r["participante"], "archivo": r["archivo"], "puntajes": r["puntajes"]} for r in puntajes])};
```

After:
```python
const PUNTAJES = {json.dumps([{"participante": r["participante"], "archivo": r["archivo"], "puntajes": r["puntajes"], "desglose": r.get("desglose", {})} for r in puntajes])};
```

**Verification**:
- Run `python3 scripts/generar_sitio.py`
- Check that `docs/index.html` contains entries with `"desglose"` key inside `PUNTAJES`
- Check that accessing `PUNTAJES[0].desglose` in JS returns the structured object (not undefined)

---

### Task 3 — Add desglose rendering JS to `verPolla()`

**Description**: Add JS code inside `verPolla()` in both `scripts/generar_sitio.py` (the template) and `docs/index.html` (the live file) to render desglose items after score bars and before bracket.

**Files affected**:
- `scripts/generar_sitio.py` — add rendering block ~line 1007 (between score bars close and bracket start)
- `docs/index.html` — add rendering block ~line 1535 (same logical position)

**Details**:

Insert after `html += '</div>';` that closes `.modal-score` (the `} else if (score)` branch) and BEFORE the bracket section (`html += '<div class="modal-section"><h4>⚽ Bracket</h4>';`).

Rendering logic (from design.md, adapted to the spec exactly):

```javascript
// ── Desglose de puntos ──
const scoreObj = findScore(polla.participante);
if (scoreObj && scoreObj.desglose) {
  const desglose = scoreObj.desglose;
  html += '<div class="modal-desglose">';
  for (const [ronda, dg] of Object.entries(desglose)) {
    if (!dg || !dg.items || !dg.items.length) continue;
    html += '<div class="dg-round">';
    html += '<div class="dg-header">' + ronda + ' · ' + dg.subtotal + ' pts</div>';
    dg.items.forEach(item => {
      const isHit = item.puntos > 0;
      const icon = isHit ? '✓' : '✗';
      const color = isHit ? '#1a6fb5' : '#dc2626';
      html += '<div class="dg-item" style="color:' + color + '">';
      html += '<span class="dg-icon">' + icon + '</span> ';
      if (item.equipo) {
        // Finales: per-position
        html += '<span class="dg-label">' + item.label + ':</span> ';
        html += '<span class="dg-team">' + item.equipo + '</span> ';
        html += '<span class="dg-pts">(' + (isHit ? '+' + item.puntos : '0') + ' pts)</span>';
      } else {
        // Regular: aciertos count
        html += '<span class="dg-label">' + item.label + ':</span> ';
        html += '<span class="dg-count">' + item.count + '</span> ';
        html += '<span class="dg-pts">= ' + item.puntos + ' pts</span>';
      }
      html += '</div>';
    });
    html += '</div>';
  }
  html += '</div>';
}
```

**NOTE**: The `scoreObj` variable name must NOT conflict with the existing `score` variable already in scope. Use a different name (e.g., `scoreObj`) or compute desglose from `score` directly (since `score` is the `puntajes` object, `scoreObj` needs to be `findScore` return — which is the raw PUNTAJES entry, not just puntajes). Actually the current `findScore` returns `p.puntajes`, NOT the full entry. So we need a separate lookup or modify `findScore` to return the full entry.

**Important design decision**: The current `findScore()` returns `p.puntajes` (the round scores dict, not the full entry). We need the full entry to access `desglose`. 

**Approach A (recommended — minimal change)**: Add desglose data directly to the `score` object returned by `findScore`. In the template, modify `findScore` to also attach desglose:
```javascript
function findScore(nombre) {
  const n = nombre.toLowerCase().trim();
  for (const p of PUNTAJES) {
    if ((p.participante||'').toLowerCase().trim() === n) {
      // Attach desglose to puntajes object
      p.puntajes.desglose = p.desglose;
      return p.puntajes;
    }
  }
  return null;
}
```
Then access as `score.desglose` in the rendering code above (using the existing `score` variable).

**Approach B**: Keep `findScore` unchanged and do a second lookup. Either works — choose Approach A as it requires fewer changes in `verPolla()`.

**Verification**:
- Run the full pipeline, open `docs/index.html`, click any participant
- Marcia Eguez modal shows "16avos · 11 pts" header, 2 desglose items in blue
- Participants with 0 in a round show that round's item in red
- Finales participants show per-position items with team names
- No JS errors in console
- Errors section at bottom: render `errores` as muted red items ONLY if the backend emits them (currently not in spec, but check fallback behavior)

---

### Task 4 — Add desglose CSS to index.html

**Description**: Add CSS classes for desglose rendering to both `scripts/generar_sitio.py` (the CSS template section) and `docs/index.html` (the live file's CSS).

**Files affected**:
- `scripts/generar_sitio.py` — add ~40 lines of CSS before `.modal-compare` (after line ~536)
- `docs/index.html` — add same CSS in the `<style>` block (after `.ms-fill div` section, before `.modal-compare`)

**Details**:

```css
.modal-desglose {
  background: #fff;
  padding: 12px;
  margin: 8px 0;
  border-radius: 8px;
}

.dg-round {
  margin-bottom: 10px;
}

.dg-header {
  font-weight: 700;
  font-size: 0.75rem;
  color: #1a3a5c;
  margin-bottom: 4px;
  border-bottom: 1px solid #eee;
  padding-bottom: 2px;
}

.dg-item {
  font-size: 0.7rem;
  padding: 2px 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.dg-icon {
  width: 14px;
  text-align: center;
  flex-shrink: 0;
}

.dg-label {
  font-weight: 500;
}

.dg-team {
  font-style: italic;
}

.dg-pts {
  font-weight: 700;
}

.dg-count {
  font-weight: 700;
}
```

**Verification**:
- Open `docs/index.html`, click a participant — desglose section renders with proper spacing, blue/red colors, and rounded white background
- No visual regression on other modal elements (bars, bracket, groups)

---

### Task 5 — Run pipeline and verify

**Description**: Execute the full data pipeline and visually verify the modal renders correctly in browser.

**Steps**:
1. Run `python3 scripts/calificar.py`
2. Run `python3 scripts/generar_sitio.py`
3. Open `docs/index.html` in browser
4. Click on at least 3 participants with different profiles

**Verification checklist**:

| Check | Expected |
|-------|----------|
| Marcia Eguez (16avos leader) | 16avos: "Aciertos de equipo: 6 (+1 c/u) = 6 pts" (blue) + "Aciertos de posición: 5 (+1 c/u) = 5 pts" (blue) → subtotal 11 |
| Carmen Carrasco | 16avos: 5 + 5 = 10 |
| Participant with 0 in a round | That round renders in red, "0 pts" |
| Finales section (when data exists) | Per-position items with team names |
| Missing desglose (backward compat) | No desglose section renders, no JS errors |
| Total scores unchanged | `puntajes.json` totals match previous run |

---

## Dependencies

```
Task 1 (calificar.py) ──> Task 2 (generar_sitio.py PUNTAJES)
Task 1 ──> Task 3 (JS rendering) ◄── Task 2
Task 3 ──> Task 4 (CSS)
Task 3 + Task 4 ──> Task 5 (verify)
```

- Task 1 must complete before Task 2 (puntajes.json must contain desglose for the generator to include it)
- Task 2 must complete before Task 3 (PUNTAJES must expose desglose for JS to render it)
- Task 3 and Task 4 are dependent (JS renders HTML with CSS classes, but technically can be done in parallel moderately safely — though better sequential since Task 3 adds HTML structure that CSS styles)
- Task 5 requires all previous tasks

## Batch Strategy

| Batch | Tasks | Rationale |
|-------|-------|-----------|
| **Batch A** | 1 | Standalone — no dependencies |
| **Batch B** | 2 | Depends only on Task 1 producing puntajes.json with desglose |
| **Batch C** | 3, 4 | Both modify the frontend; Task 3 adds markup that Task 4 styles. Can run in one apply session (modify template, modify live file) |
| **Batch D** | 5 | Requires all previous tasks completed |

**Recommended sdd-apply calls**: 4 total (one per batch).

## Review Workload Forecast

| File | Change type | Estimated lines added/modified |
|------|-------------|-------------------------------|
| `scripts/calificar.py` | New function + integration call | ~72 lines (+70 new function, +2 call) |
| `scripts/generar_sitio.py` | 3 changes (line 901, JS block ~1007, CSS block ~536) | ~50 lines total (+1 PUNTAJES, ~40 CSS, ~30 JS rendering with template escaping) |
| `docs/index.html` | 2 changes (JS block ~1535, CSS block after ms-fill) | ~70 lines total (~30 JS, ~40 CSS) |

**Total estimated delta**: ~192 lines across 3 files.

### Review notes

- **Task 1** (calificar.py): Focus on the parsing regex for finales strings and empty/edge cases. Verify subtotals match puntajes.
- **Task 2** (generar_sitio.py line 901): Small change — mainly confirm the key name matches what Task 1 emits.
- **Task 3** (JS): Verify template escaping (double `{{` → `{`) in generar_sitio.py. The live `docs/index.html` uses single braces. Ensure both files are edited identically modulo escaping. Critical: verify `findScore()` modification shares the desglose data correctly.
- **Task 4** (CSS): Verify no selector conflicts with existing modal classes. The `.dg-` prefix is unique.
