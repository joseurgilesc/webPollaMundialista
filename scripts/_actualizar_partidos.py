#!/usr/bin/env python3
"""Genera data/resultados_reales.json con partidos manuales actualizados hasta 15 de junio."""
import sys, json
from pathlib import Path

# ── Mapping: nombre inglés → nombre polla ──
EN_TO_POLLA = {
    "Mexico": "🇲🇽 MÉXICO", "South Africa": "🇿🇦 SUDÁFRICA", "South Korea": "🇰🇷 COREA DEL SUR",
    "Czech Republic": "🇨🇿 REP. CHECA", "Canada": "🇨🇦 CANADÁ", "Bosnia and Herzegovina": "🇧🇦 BOSNIA Y HERZEGOVINA",
    "Qatar": "🇶🇦 QATAR", "Switzerland": "🇨🇭 SUIZA", "Brazil": "🇧🇷 BRASIL", "Morocco": "🇲🇦 MARRUECOS",
    "Haiti": "🇭🇹 HAITÍ", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿 ESCOCIA", "United States": "🇺🇸 ESTADOS UNIDOS",
    "Paraguay": "🇵🇾 PARAGUAY", "Australia": "🇦🇺 AUSTRALIA", "Turkey": "🇹🇷 TURQUÍA",
    "Germany": "🇩🇪 ALEMANIA", "Curacao": "CURAÇAO", "Côte d'Ivoire": "🇨🇮 COSTA DE MARFIL",
    "Ivory Coast": "🇨🇮 COSTA DE MARFIL", "Ecuador": "🇪🇨 ECUADOR", "Netherlands": "🇳🇱 HOLANDA",
    "Japan": "🇯🇵 JAPÓN", "Sweden": "🇸🇪 SUECIA", "Tunisia": "🇹🇳 TÚNEZ", "Belgium": "🇧🇪 BÉLGICA",
    "Egypt": "🇪🇬 EGIPTO", "Iran": "🇮🇷 IRÁN", "New Zealand": "🇳🇿 NUEVA ZELANDA",
    "Spain": "🇪🇸 ESPAÑA", "Cape Verde": "🇨🇻 CABO VERDE", "Saudi Arabia": "🇸🇦 ARABIA SAUDÍ",
    "Uruguay": "🇺🇾 URUGUAY", "France": "🇫🇷 FRANCIA", "Senegal": "🇸🇳 SENEGAL", "Iraq": "🇮🇶 IRAK",
    "Norway": "🇳🇴 NORUEGA", "Argentina": "🇦🇷 ARGENTINA", "Algeria": "🇩🇿 ARGELIA",
    "Austria": "🇦🇹 AUSTRIA", "Jordan": "🇯🇴 JORDANIA", "Portugal": "🇵🇹 PORTUGAL",
    "DR Congo": "🇨🇩 REP. CONGO", "Congo DR": "🇨🇩 REP. CONGO", "Uzbekistan": "🇺🇿 UZBEKISTÁN",
    "Colombia": "🇨🇴 COLOMBIA", "England": "🇬🇧 INGLATERRA", "Croatia": "🇭🇷 CROACIA",
    "Ghana": "🇬🇭 GHANA", "Panama": "🇵🇦 PANAMÁ",
}

def n(name):
    return EN_TO_POLLA.get(name, name.upper())

# ── Grupo → equipos ──
GROUP_TEAMS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curacao", "Côte d'Ivoire", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Spain", "Cape Verde", "Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Saudi Arabia", "Uruguay", "France", "Senegal", "Iraq", "Norway"],
    "I": ["Argentina", "Algeria", "Austria", "Jordan"],
    "J": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "K": ["England", "Croatia", "Ghana", "Panama"],
}

# Revisar: según los datos de la API, los grupos son A-L con 4 equipos cada uno.
# Ajusto a 4 por grupo:
GROUP_TEAMS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curacao", "Côte d'Ivoire", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Spain", "Cape Verde", "Belgium", "Egypt"],
    "H": ["Iran", "New Zealand", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

# ── Partidos: (grupo, local, goles_local, visitante, goles_visitante) ──
MATCHES = [
    # 11 de junio
    ("A", "Mexico", 2, "South Africa", 0),
    ("A", "South Korea", 2, "Czech Republic", 1),
    # 12 de junio
    ("B", "Canada", 1, "Bosnia and Herzegovina", 1),
    ("D", "United States", 4, "Paraguay", 1),
    # 13 de junio
    ("B", "Qatar", 1, "Switzerland", 1),
    ("C", "Brazil", 1, "Morocco", 1),
    ("C", "Haiti", 0, "Scotland", 1),
    # 14 de junio
    ("D", "Australia", 2, "Turkey", 0),
    ("E", "Germany", 7, "Curacao", 1),
    ("F", "Netherlands", 2, "Japan", 2),
    ("E", "Côte d'Ivoire", 1, "Ecuador", 0),
    ("F", "Sweden", 5, "Tunisia", 1),
    # 15 de junio
    ("G", "Spain", 0, "Cape Verde", 0),
    ("G", "Belgium", 1, "Egypt", 1),
    ("H", "Saudi Arabia", 1, "Uruguay", 1),
    ("H", "Iran", 2, "New Zealand", 2),
]

# ── Calcular stats ──
from collections import defaultdict
stats = defaultdict(lambda: {"pts": 0, "gf": 0, "ga": 0, "played": 0})
group_names = defaultdict(set)

for grp, home, hs, away, aw in MATCHES:
    hn = n(home); an = n(away)
    group_names[grp].add(hn); group_names[grp].add(an)
    stats[(grp, hn)]["gf"] += hs; stats[(grp, hn)]["ga"] += aw; stats[(grp, hn)]["played"] += 1
    stats[(grp, an)]["gf"] += aw; stats[(grp, an)]["ga"] += hs; stats[(grp, an)]["played"] += 1
    if hs > aw: stats[(grp, hn)]["pts"] += 3
    elif aw > hs: stats[(grp, an)]["pts"] += 3
    else: stats[(grp, hn)]["pts"] += 1; stats[(grp, an)]["pts"] += 1

# ── Ordenar grupos por FIFA (PTS > GD > GF > manual) ──
# Para los grupos sin empates (A, D, G, H: no hay datos suficientes para ordenar),
# los grupos E y F tienen equipos con 0 partidos (no se ordenan),
# los grupos con empate no resoluble:
#   B: todos 1pt/0GD/1GF → manual
#   C: BRA/MAR 1pt/0GD/1GF, ESCO 3pt/+1GD/1GF, HAITI 0pt → ESCO 1°, HAITI 4°, BRA/MAR empatados → manual

def sort_group(grp, tids):
    """Simple sort by PTS > GD > GF. For ties that H2H doesn't resolve, ask."""
    from itertools import groupby
    tl = []
    for t in tids:
        s = stats[(grp, t)]
        tl.append([t, s["pts"], s["gf"] - s["ga"], s["gf"]])
    tl.sort(key=lambda x: (-x[1], -x[2], -x[3]))
    
    # Resolve ties with H2H
    resolved = []
    for _, tie_group in groupby(tl, key=lambda x: (x[1], x[2], x[3])):
        tg = list(tie_group)
        if len(tg) <= 1:
            resolved.extend(tg)
            continue
        # H2H between tied teams
        tied_names = {t[0] for t in tg}
        h2h = {t[0]: {"pts": 0, "gf": 0, "ga": 0} for t in tg}
        for grp2, home, hs, away, aw in MATCHES:
            hn = n(home); an = n(away)
            if hn not in tied_names or an not in tied_names:
                continue
            h2h[hn]["gf"] += hs; h2h[hn]["ga"] += aw
            h2h[an]["gf"] += aw; h2h[an]["ga"] += hs
            if hs > aw: h2h[hn]["pts"] += 3
            elif aw > hs: h2h[an]["pts"] += 3
            else: h2h[hn]["pts"] += 1; h2h[an]["pts"] += 1
        
        tg.sort(key=lambda t: (-h2h[t[0]]["pts"], -(h2h[t[0]]["gf"] - h2h[t[0]]["ga"]), -h2h[t[0]]["gf"]))
        
        # Check if resolved
        h2h_unique = set((h2h[t[0]]["pts"], h2h[t[0]]["gf"] - h2h[t[0]]["ga"], h2h[t[0]]["gf"]) for t in tg)
        if len(h2h_unique) == len(tg):
            resolved.extend(tg)
        else:
            print(f"\n  ⚠️  Empate no resoluble en Grupo {grp}:")
            for i, t in enumerate(tg):
                h = h2h[t[0]]
                print(f"      {i+1}. {t[0]} — PTS={t[1]} GD={t[2]} GF={t[3]} | H2H: {h['pts']}pts ({h['gf']}-{h['ga']})")
            print(f"  🔗 https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/standings")
            inp = input(f"  Orden (1={tg[0][0]}..{len(tg)}={tg[-1][0]}, ej: 1,2,3,4): ").strip()
            indices = [int(x.strip()) for x in inp.split(",")]
            resolved.extend([tg[i-1] for i in indices])
    
    return {tid: rank+1 for rank, (tid, *_) in enumerate(resolved)}

# ── Build resultado ──
grupos_result = {}
for grp in sorted(GROUP_TEAMS.keys()):
    tids = [n(t) for t in GROUP_TEAMS[grp]]
    ranked = sort_group(grp, tids)
    grupos_result[grp] = ranked

# Build stats for output
api_stats = {}
for (grp, name), s in stats.items():
    api_stats.setdefault(grp, {})[name] = {"pts": s["pts"], "gf": s["gf"], "ga": s["ga"]}

# ── 16avos ──
SLOTS_16AVOS = [
    ("1E", 1, "E"), ("3 ABCDF", 3, ["A","B","C","D","F"]), ("1I", 1, "I"), ("3 CDFGH", 3, ["C","D","F","G","H"]),
    ("2A", 2, "A"), ("2B", 2, "B"), ("1F", 1, "F"), ("2C", 2, "C"),
    ("2K", 2, "K"), ("2L", 2, "L"), ("1H", 1, "H"), ("2J", 2, "J"),
    ("1D", 1, "D"), ("3 BEFIJ", 3, ["B","E","F","I","J"]), ("1G", 1, "G"), ("3 AEFHIJ", 3, ["A","E","F","H","I","J"]),
    ("1C", 1, "C"), ("2F", 2, "F"), ("2E", 2, "E"), ("2I", 2, "I"),
    ("1A", 1, "A"), ("3 CEFHI", 3, ["C","E","F","H","I"]), ("1L", 1, "L"), ("3 EHIJK", 3, ["E","H","I","J","K"]),
    ("1J", 1, "J"), ("2H", 2, "H"), ("2D", 2, "D"), ("2G", 2, "G"),
    ("1B", 1, "B"), ("3 EFGIJ", 3, ["E","F","G","I","J"]), ("1K", 1, "K"), ("3 DEIJL", 3, ["D","E","I","J","L"]),
]

def get_third_place_team(grp, grupos):
    """Get the 3rd place team from a group."""
    for eq, r in grupos.get(grp, {}).items():
        if r == 3:
            return eq
    return ""

# Terceros: solo grupos con ≥1 partido
terceros = []
for grp_letra in sorted(grupos_result.keys()):
    ranked = list(grupos_result[grp_letra].items())
    has_played = any(stats.get((grp_letra, eq), {}).get("played", 0) > 0 for eq, _ in ranked)
    if not has_played:
        continue
    if len(ranked) >= 3:
        eq_name = ranked[2][0]
        ss = stats.get((grp_letra, eq_name), {})
        terceros.append((grp_letra, ss["pts"], ss["gf"] - ss["ga"], eq_name))

# Top 8 terceros
terceros.sort(key=lambda x: (-x[1], -x[2]))
terceros_clasificados = {t[0] for t in terceros[:8]}

ronda_16 = []
for slot, pos, grp in SLOTS_16AVOS:
    equipo = ""
    if pos in (1, 2) and isinstance(grp, str) and grp in grupos_result:
        for eq, r in grupos_result[grp].items():
            if r == pos:
                equipo = eq
                break
    elif isinstance(grp, list):
        for g in grp:
            if g not in grupos_result:
                continue
            eq = get_third_place_team(g, grupos_result)
            # Verify it's among top 8
            has_played = any(
                stats.get((g, e), {}).get("played", 0) > 0
                for e, _ in grupos_result[g].items()
            )
            if eq and has_played and g in terceros_clasificados:
                equipo = eq
                break
    ronda_16.append({"slot": slot, "equipo": equipo})

resultado = {
    "_nota": "Datos actualizados manualmente hasta 15 de junio 2026",
    "_stats": dict(api_stats),
    "grupos": grupos_result,
    "ronda_16avos": ronda_16,
    "ronda_8avos": [],
    "ronda_cuartos": [],
    "ronda_semifinales": [],
    "finales": {"campeon": "", "segundo": "", "tercero": "", "cuarto": ""},
}

# Save
path = Path("data/resultados_reales.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)

eq16 = sum(1 for e in ronda_16 if e["equipo"])
print(f"✅ {eq16}/32 equipos en 16avos")
print(f"✅ {len(MATCHES)} partidos procesados en {len([g for g in grupos_result if any(stats.get((g,e),{}).get('played',0)>0 for e in grupos_result[g])])} grupos activos")
print(f"💾 Guardado en {path}")
