# FIFA Group Sort Specification

## Purpose

Group standings produced by the pipeline MUST match FIFA Article 13 tiebreaker criteria (PTS > GD > GF > H2H pts > H2H GD > H2H GF). Best third-placed team selection MUST derive from the same engine so that rankings are consistent across the tournament bracket.

## Requirements

### Requirement: FIFA-compliant group ranking

The system MUST sort teams within each group using the following criteria in exact order:
1. Total points (PTS), descending
2. Goal difference (GD), descending
3. Goals for (GF), descending
4. Head-to-head points between tied teams (H2H pts), descending
5. Head-to-head goal difference between tied teams (H2H GD), descending
6. Head-to-head goals for between tied teams (H2H GF), descending
7. Remaining ties (fair play / drawing of lots) MUST be resolved via interactive manual prompt

#### Scenario: Basic sort by PTS > GD > GF

- GIVEN a group with 4 teams having different points totals
- WHEN `_sort_group()` is called for that group
- THEN teams are ranked by PTS descending, with GD and GF as secondary and tertiary keys

#### Scenario: Head-to-head resolution for tied teams

- GIVEN a group where 2 or more teams share the same (PTS, GD, GF) tuple
- WHEN their subgroup is isolated by `groupby`
- THEN `_h2h_scores()` computes H2H points, GD, and GF using only matches between the tied teams
- AND those tied teams are re-ranked by H2H criteria 4-6

#### Scenario: Manual tiebreaker for unresolvable ties

- GIVEN a tie subgroup where after H2H sorting, some teams remain indistinguishable (same (H2H pts, H2H GD, H2H GF))
- THEN the engine SHALL print each tied team's full stats and a FIFA.com reference link
- AND SHALL prompt the operator to input a manual ranking
- AND MUST validate the input (exactly N integers, 1..N, no repeats) before accepting

#### Scenario: Unfinished groups return flat rank-0

- GIVEN a group where no team has a played match (`has_finished` is `false`)
- WHEN `_sort_group()` is called
- THEN every team SHALL receive rank 0

### Requirement: Best third-placed team selection

The system MUST derive the best third-placed teams from `grupos_result`, which already holds the FIFA-sorted order. It MUST rank third-placed teams by (PTS > GD > GF) across groups.

#### Scenario: Third-place ranking uses sorted group order

- GIVEN `grupos_result` with complete FIFA-sorted rankings for every group
- WHEN the engine selects the top 8 third-placed teams
- THEN each third-place entry is the team at rank 3 within its group
- AND the 8 qualifiers are determined by sorting (PTS descending, GD descending, GF descending)

#### Scenario: Bracket slot assignment from sorted results

- GIVEN each phase of the tournament bracket
- WHEN filling 1st/2nd-place slots
- THEN the engine SHALL read the team at rank N from `grupos_result[group]`

### Requirement: Interactive tiebreaker input validation

The manual prompt SHALL accept comma-separated integer rankings (e.g. `2,1,3,4`) and MUST reject invalid or out-of-range input with a descriptive error.

#### Scenario: Valid input accepted

- GIVEN the engine expects a ranking of 3 tied teams
- WHEN the operator enters `3,1,2`
- THEN the sort order is updated to match that sequence
- AND execution continues

#### Scenario: Invalid input rejected

- GIVEN the engine expects a ranking of 3 tied teams
- WHEN the operator enters `1,2` or `1,2,3,4` or `a,b,c`
- THEN the engine prints an error message and re-prompts
