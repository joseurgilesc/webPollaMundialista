# Design: desglose-puntos-modal

## Overview

Add a structured points breakdown (desglose) inside the participant detail modal.
The desglose is computed from existing `detalle` data — no new scoring logic.

## Architecture

### Data Flow

```
calificar.py ──> puntajes.json ──> generar_sitio.py ──> docs/index.html
     │                                                       │
     └── adds desglose field          ┌──────────────────────┘
                                     ▼
                              PUNTAJES constant
                              (now includes desglose)
                              │
                              ▼
                         verPolla() renders
                         desglose after bars
                         before bracket
```

### No new dependencies

- Python stdlib only (json module)
- No JS frameworks, no build tools

## Changes

### 1. `scripts/calificar.py` — Add desglose computation

A new function `_computar_desglose(puntajes: dict, detalle: dict) -> dict` that
reads existing `detalle` per round and returns a structured `desglose` dict.

Called inside `calificar_polla()` after existing scoring loops, before returning
the result dict.

#### desglose JSON structure

```jsonc
{
  "participante": "Marcia Eguez Álvarez",
  "puntajes": { "16avos": 11, ... },
  "detalle": { /* existing - unchanged */ },
  "desglose": {
    "16avos": {
      "items": [
        { "label": "Aciertos de equipo", "puntos": 6, "count": 6, "detalle": "6 (+1 c/u)" },
        { "label": "Aciertos de posición", "puntos": 5, "count": 5, "detalle": "5 (+1 c/u)" }
      ],
      "subtotal": 11
    },
    "8avos": {
      "items": [
        { "label": "Aciertos", "puntos": 0, "count": 0, "detalle": "0 (×2 pts)" }
      ],
      "subtotal": 0
    },
    "cuartos": {
      "items": [
        { "label": "Aciertos", "puntos": 9, "count": 3, "detalle": "3 (×3 pts)" }
      ],
      "subtotal": 9
    },
    "semifinales": {
      "items": [
        { "label": "Aciertos", "puntos": 0, "count": 0, "detalle": "0 (×4 pts)" }
      ],
      "subtotal": 0
    },
    "finales": {
      "items": [
        { "label": "Campeón", "puntos": 20, "equipo": "ARGENTINA", "hit": true },
        { "label": "Segundo", "puntos": 11, "equipo": "BRASIL", "hit": true },
        { "label": "Tercero", "puntos": 0, "equipo": "ALEMANIA", "hit": false },
        { "label": "Cuarto", "puntos": 5, "equipo": "URUGUAY", "hit": true }
      ],
      "subtotal": 36
    }
  }
}
```

#### Round-specific computation logic

| Round | Source data | Items |
|-------|-------------|-------|
| 16avos | `detalle["16avos"]["aciertos_equipo"]`, `aciertos_posicion[]` | 2 items: equipo count + posicion count (1pt each) |
| 8avos | `detalle["8avos"]["aciertos"]` | 1 item: count (×2 pts each) |
| cuartos | `detalle["cuartos"]["aciertos"]` | 1 item: count (×3 pts each) |
| semifinales | `detalle["semifinales"]["aciertos"]` | 1 item: count (×4 pts each) |
| finales | `detalle["finales"]["aciertos"]` (parsed strings like `"campeon: ARGENTINA (+20)"`) | 4 items: per-position results |

For finales, parse the `detalle["finales"]["aciertos"]` strings to extract
position, team, and points. Strings follow the format:
`"{puesto}: {equipo} (+{pts})"` for hits,
`"{puesto}: predijo {equipo}, real: {real} (0 pts)"` for misses.

#### Edge cases

- Empty/missing detalle for a round → `{items: [{label: "Aciertos", puntos: 0, count: 0, detalle: "Sin datos"}], subtotal: 0}`
- `detalle` key missing entirely → return empty `desglose: {}`

### 2. `scripts/generar_sitio.py` — Pass desglose to frontend

**Line 901 change**: Include `desglose` in the PUNTAJES constant.

Before:
```python
const PUNTAJES = {json.dumps([{"participante": r["participante"], "archivo": r["archivo"], "puntajes": r["puntajes"]} for r in puntajes])};
```

After:
```python
const PUNTAJES = {json.dumps([{"participante": r["participante"], "archivo": r["archivo"], "puntajes": r["puntajes"], "desglose": r.get("desglose", {})} for r in puntajes])};
```

### 3. `docs/index.html` — Render desglose in modal

Inside `verPolla()`, after the score bars section (after line 1535 in current
`index.html`, after line ~1010 in `generar_sitio.py` template), add desglose
rendering.

#### Render logic

```javascript
// ── Desglose de puntos ──
const score = findScore(polla.participante);
if (score && score.desglose) {
  html += '<div class="modal-desglose">';
  for (const [ronda, dg] of Object.entries(score.desglose)) {
    if (!dg || !dg.items || !dg.items.length) continue;
    html += '<div class="dg-round">';
    html += '<div class="dg-header">' + ronda + ' · ' + dg.subtotal + ' pts</div>';
    dg.items.forEach(item => {
      const isHit = item.puntos > 0;
      const icon = isHit ? '✓' : '✗';
      const color = isHit ? 'var(--azul-hit, #1a6fb5)' : 'var(--rojo-miss, #dc2626)';
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

#### CSS (add to existing styles)

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
  color: var(--navy, #1a3a5c);
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

CSS variables expected to already exist (or added):
- `--azul-hit: #1a6fb5` (blue for hits)
- `--rojo-miss: #dc2626` (red for misses)
- `--navy: #1a3a5c` (already used in modal)

#### Placement in modal

```
1. Finales cards (prediction vs real)             ← existing
2. Score bars + total                             ← existing
3. [NEW] Desglose section                         ← ADDED
4. Bracket table                                  ← existing
5. Grupos                                         ← existing
```

#### Graceful degradation

- If `score.desglose` is undefined/null → no desglose section renders
- If a round's desglose is missing → that round is skipped
- If desglose exists but `items` is empty → round is skipped

## Testing

### Manual test cases

Run `python3 scripts/calificar.py && python3 scripts/generar_sitio.py` and open
`docs/index.html` in browser. Click on participants and verify:

1. **Marcia Eguez**: 16avos shows "Aciertos de equipo: 6 (+1 c/u) = 6 pts" (blue) + "Aciertos de posición: 5 (+1 c/u) = 5 pts" (blue) → subtotal 11
2. **Carmen Carrasco**: 16avos shows 5 + 5 = 10
3. **Participants with 0 in a round**: that round shows 0 items in red
4. **Backward compat**: old puntajes.json without desglose still renders modal without errors

### Verification command

```bash
python3 scripts/calificar.py && python3 scripts/generar_sitio.py
```

Then visually verify in the browser.

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Modal too tall with desglose | Low-med | Existing max-height:65vh + overflow-y:auto handles it |
| Missing desglose breaks modal | Low | Graceful fallback — check existence before rendering |
| Finales parsing fragile | Low | Match by existing string format from calificar.py |
