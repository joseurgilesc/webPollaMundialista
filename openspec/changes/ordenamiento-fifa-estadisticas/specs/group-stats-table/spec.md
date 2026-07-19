# Group Stats Table Specification

## Purpose

Team statistics (PTS, GF, GA, GD) inside the participant modal MUST render as an aligned HTML table instead of inline text, so that users can scan and compare standings at a glance.

## Requirements

### Requirement: Stats table in participant modal

The system MUST render a `<table class="stats-table">` inside the `mg-real` section of every group in the participant modal. The table header MUST show `# | Eq | PTS | GF | GA | GD`. Each row SHALL show the team's rank, name, and corresponding stats.

#### Scenario: Table renders for a group with real data

- GIVEN a participant modal is opened for a group with real standings in `REALES.grupos[g]`
- WHEN the modal renders
- THEN a `<table class="stats-table">` appears below the "Real" label
- AND the table header contains columns `#`, `Eq`, `PTS`, `GF`, `GA`, `GD`
- AND each team row shows its position, name, and stats values

#### Scenario: Stats cell is empty when no stats exist

- GIVEN a group exists in `REALES.grupos` but has no entry in `REALES._stats`
- WHEN the modal renders
- THEN the PTS/GF/GA/GD cells for that team SHALL be empty strings

#### Scenario: GD displays with sign prefix

- GIVEN a team has goal difference computed as `gf - ga`
- WHEN the GD cell renders
- THEN positive values SHALL display with a `+` prefix (e.g., `+3`)
- AND negative values SHALL display with a `-` prefix (e.g., `-1`)
- AND zero SHALL display as `0`

### Requirement: Stats table styling

The stats table MUST apply CSS via the `.stats-table`, `.stats-table th`, and `.stats-table td` selectors, with compact font sizes and minimal padding to fit within the modal card without overflow.

#### Scenario: Table fits within modal card

- GIVEN the modal card width is approximately 220px
- WHEN the stats table renders
- THEN table width is 100% of the parent container
- AND font sizes do not exceed 0.65rem for cells and 0.55rem for headers
- AND column headers are centered

### Requirement: Header rendering from CSS only (Python template)

The Python `generar_publica()` template MUST include the `.stats-table` CSS rules within the inline `<style>` block, so that generated HTML pages have the styling embedded without external dependencies.

#### Scenario: CSS present in generated output

- GIVEN `generar_sitio.py` runs with the `--publica` flag
- WHEN the generated `index.html` is inspected
- THEN it contains `.modal-grupo .stats-table`, `.modal-grupo .stats-table th`, and `.modal-grupo .stats-table td` rule blocks
- AND each rule block specifies the expected font-size, padding, and alignment values
