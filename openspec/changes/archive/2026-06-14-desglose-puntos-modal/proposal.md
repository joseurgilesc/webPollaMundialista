# Proposal: desglose-puntos-modal

## Intent

Participants see only total score per round in the modal (e.g., "16avos: 11 pts"). No breakdown of HOW points were earned — team hits vs position hits in 16avos, individual aciertos in later rounds, per-position points in finales. This obscures scoring logic and reduces trust.

Add a structured desglose (breakdown) inside the modal so each round shows exactly which predictions scored and why.

## Scope

### In Scope
- Modify `calificar.py` to emit structured desglose data per round in `puntajes.json`
- Modify `generar_sitio.py` to pass desglose to frontend (currently strips `detalle` at line 901)
- Modify `docs/index.html` to render the desglose in the participant modal
- Spanish labels, azul/rojo scheme, white background

### Out of Scope
- Card summary changes, JS frameworks, testing infra, admin modal, reactive data

## Capabilities

### New Capabilities
- `puntajes-desglose`: structured per-round breakdown with items grouped by type, per-item points, and subtotals

### Modified Capabilities
- None (no existing specs)

## Approach

1. **calificar.py**: `detalle` already has raw data (`aciertos_equipo[]`, `aciertos_posicion[]` for 16avos; `aciertos[]` for other rounds; per-position strings for finales). Add computed `desglose` with `items[]` (`{label, puntos}`) and `subtotal`. No new scoring logic.

2. **generar_sitio.py**: Include full `detalle` in embedded `PUNTAJES` JS (currently stripped).

3. **index.html**: After score bars, render desglose per round:
   - 16avos: "Aciertos de equipo: N (+1 c/u)" + "Aciertos de posición: M (+1 c/u)" → subtotal
   - 8avos/Cuartos/Semis: "Aciertos: N" with list → subtotal
   - Finales: Per-position rows (Campeón +20, etc.) → subtotal
   - Errors in muted red below. Azul hits, rojo misses.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `scripts/calificar.py` | Modified | Add `desglose` per round |
| `scripts/generar_sitio.py` | Modified | Pass `detalle` to JS |
| `docs/index.html` | Modified | Render desglose + CSS |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Modal too tall | Med | Existing max-height/overflow; collapse behind toggle if needed |
| HTML size increase | Low | ~200B/participant × 96 = ~19KB — negligible |

## Rollback Plan

Revert three files to previous commits. No data migration — desglose is computed, not ground truth.

## Dependencies

None.

## Success Criteria

- [ ] Marcia Eguez: "6 aciertos de equipo (+1 c/u)" + "5 aciertos de posición (+1 c/u)" = 11 pts in 16avos
- [ ] Carmen Carrasco: "5 aciertos de equipo (+1 c/u)" + "5 aciertos de posición (+1 c/u)" = 10 pts in 16avos
- [ ] 8avos/Cuartos/Semis show "Aciertos: N" with team names and subtotal
- [ ] Finales show per-position hits with point values
- [ ] Modal loads without errors, desglose renders inside existing scroll container
