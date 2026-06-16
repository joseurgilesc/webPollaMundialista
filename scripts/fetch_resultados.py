#!/usr/bin/env python3
"""
Obtiene resultados reales del Mundial 2026 desde worldcup26.ir.

Flujo:
1. Obtiene standings de grupos → equipos clasificados a 16avos
2. Mapea equipos a slots del bracket FIFA
3. Sigue resultados de partidos KO → llena 8avos, cuartos, semis, finales
4. Guarda en data/resultados_reales.json

Uso:
  python3 fetch_resultados.py           # API → actualiza JSON
  python3 fetch_resultados.py --api     # solo API
  python3 fetch_resultados.py --manual  # validar JSON manual
"""

import json, os, re, sys, urllib.request, urllib.error
from pathlib import Path

API_BASE = "https://worldcup26.ir"
RESULTADOS_FILE = Path("data/resultados_reales.json")

# ── Mapeo nombres API → polla ──
EN_TO_POLLA = {
    "Mexico": "🇲🇽 MÉXICO", "South Africa": "🇿🇦 SUDÁFRICA", "South Korea": "🇰🇷 COREA DEL SUR",
    "Czech Republic": "🇨🇿 REP. CHECA", "Canada": "🇨🇦 CANADÁ", "Bosnia and Herzegovina": "🇧🇦 BOSNIA Y HERZEGOVINA",
    "Qatar": "🇶🇦 QATAR", "Switzerland": "🇨🇭 SUIZA", "Brazil": "🇧🇷 BRASIL", "Morocco": "🇲🇦 MARRUECOS",
    "Haiti": "🇭🇹 HAITÍ", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿 ESCOCIA", "United States": "🇺🇸 ESTADOS UNIDOS",
    "Paraguay": "🇵🇾 PARAGUAY", "Australia": "🇦🇺 AUSTRALIA", "Turkey": "🇹🇷 TURQUÍA",
    "Germany": "🇩🇪 ALEMANIA", "Curacao": "🇨🇼 CURAZAO", "Côte d'Ivoire": "🇨🇮 COSTA DE MARFIL",
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

# ── Slots del bracket FIFA 2026 (mapeados de los Excels) ──
# Cada entrada: (slot_code, group_position, group_letter)
# Para "mejores terceros": lista de grupos posibles
SLOTS_16AVOS = [
    # Lado izquierdo
    ("1E", 1, "E"), ("3 ABCDF", 3, ["A","B","C","D","F"]), ("1I", 1, "I"), ("3 CDFGH", 3, ["C","D","F","G","H"]),
    ("2A", 2, "A"), ("2B", 2, "B"), ("1F", 1, "F"), ("2C", 2, "C"),
    ("2K", 2, "K"), ("2L", 2, "L"), ("1H", 1, "H"), ("2J", 2, "J"),
    ("1D", 1, "D"), ("3 BEFIJ", 3, ["B","E","F","I","J"]), ("1G", 1, "G"), ("3 AEFHIJ", 3, ["A","E","F","H","I","J"]),
    # Lado derecho
    ("1C", 1, "C"), ("2F", 2, "F"), ("2E", 2, "E"), ("2I", 2, "I"),
    ("1A", 1, "A"), ("3 CEFHI", 3, ["C","E","F","H","I"]), ("1L", 1, "L"), ("3 EHIJK", 3, ["E","H","I","J","K"]),
    ("1J", 1, "J"), ("2H", 2, "H"), ("2D", 2, "D"), ("2G", 2, "G"),
    ("1B", 1, "B"), ("3 EFGIJ", 3, ["E","F","G","I","J"]), ("1K", 1, "K"), ("3 DEIJL", 3, ["D","E","I","J","L"]),
]

def _api_get(endpoint):
    url = f"{API_BASE}/{endpoint}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  ⚠️  Error API: {e}")
        return None

def _en_to_polla(n):
    return EN_TO_POLLA.get(n, n.upper())

def build_results_from_api():
    print("🌐 Consultando worldcup26.ir...")
    teams = _api_get("get/teams")
    groups = _api_get("get/groups")
    games = _api_get("get/games")
    if not all([teams, groups, games]):
        print("  ❌ Datos incompletos"); return None
    
    tl = teams.get("teams", teams) if isinstance(teams, dict) else teams
    gl = groups.get("groups", groups) if isinstance(groups, dict) else groups
    gm = games.get("games", games) if isinstance(games, dict) else games
    
    print(f"  ✅ {len(tl)} equipos, {len(gl)} grupos, {len(gm)} partidos")
    
    # Team ID → nombre polla
    id_name = {str(t["id"]): _en_to_polla(t.get("name_en","")) for t in tl}
    
    # ── Calcular standings desde partidos (más confiable que /get/groups) ──
    from collections import defaultdict
    
    # Inicializar estadísticas por grupo y equipo
    stats = defaultdict(lambda: {"pts": 0, "gf": 0, "ga": 0, "played": 0})
    group_teams = defaultdict(set)
    
    for m in gm:
        if m.get("type") != "group":
            continue
        grp = m.get("group", "")
        if not grp:
            continue
        hid = str(m.get("home_team_id", ""))
        aid = str(m.get("away_team_id", ""))
        group_teams[grp].add(hid)
        group_teams[grp].add(aid)
        
        if m.get("finished") != "TRUE":
            continue
        
        hs = int(m.get("home_score", 0) or 0)
        aw = int(m.get("away_score", 0) or 0)
        
        stats[(grp, hid)]["gf"] += hs
        stats[(grp, hid)]["ga"] += aw
        stats[(grp, hid)]["played"] += 1
        stats[(grp, aid)]["gf"] += aw
        stats[(grp, aid)]["ga"] += hs
        stats[(grp, aid)]["played"] += 1
        
        if hs > aw:
            stats[(grp, hid)]["pts"] += 3
        elif aw > hs:
            stats[(grp, aid)]["pts"] += 3
        else:
            stats[(grp, hid)]["pts"] += 1
            stats[(grp, aid)]["pts"] += 1
    
    # ── Head-to-Head calculator ──
    def _h2h_scores(grp, tids_pool, team_list_raw):
        """Calcula H2H pts, GD, GF entre tids_pool.
        
        team_list_raw: lista de (tid, pts, gd, gf) para el grupo completo
        (necesaria porque el H2H incluye SOLO partidos entre los empatados).
        """
        h2h = {tid: {"pts": 0, "gf": 0, "ga": 0} for tid in tids_pool}
        for m in gm:
            if m.get("type") != "group" or m.get("group") != grp:
                continue
            if m.get("finished") != "TRUE":
                continue
            hid = str(m.get("home_team_id", ""))
            aid = str(m.get("away_team_id", ""))
            if hid not in tids_pool or aid not in tids_pool:
                continue  # No es partido entre empatados
            hs = int(m.get("home_score", 0) or 0)
            aw = int(m.get("away_score", 0) or 0)
            h2h[hid]["gf"] += hs
            h2h[hid]["ga"] += aw
            h2h[aid]["gf"] += aw
            h2h[aid]["ga"] += hs
            if hs > aw:
                h2h[hid]["pts"] += 3
            elif aw > hs:
                h2h[aid]["pts"] += 3
            else:
                h2h[hid]["pts"] += 1
                h2h[aid]["pts"] += 1
        return h2h

    def _fifa_sort_key(item):
        """Retorna tupla para orden FIFA: pts, gd, gf (negativo = descendente).
        El H2H se resuelve por fuera con grouping."""
        tid, pts, gd, gf = item
        return (-pts, -gd, -gf)

    def _sort_group(grp, tids, has_finished):
        """Ordena equipos de un grupo usando criterios FIFA completos.
        Devuelve lista de (tid, rank) ordenada.
        Si hay empates no resolubles, pregunta en consola."""
        if not has_finished:
            return [(tid, 0) for tid in tids]
        
        # Lista base
        team_list = []
        for tid in tids:
            s = stats[(grp, tid)]
            team_list.append([tid, s["pts"], s["gf"] - s["ga"], s["gf"]])
        
        # Paso 1: orden por FIFA criteria 1-3 (PTS > GD > GF)
        team_list.sort(key=_fifa_sort_key)
        
        # Paso 2: resolver empates con H2H (FIFA criteria 4-6)
        # Agrupar por tupla (pts, gd, gf) — los que empatan en 1-3
        from itertools import groupby
        resolved = []
        for _, tie_group in groupby(team_list, key=lambda x: (x[1], x[2], x[3])):
            tie_group = list(tie_group)
            if len(tie_group) <= 1:
                resolved.extend(tie_group)
                continue
            
            # Hay empate — calcular H2H entre estos equipos
            tied_tids = [t[0] for t in tie_group]
            h2h = _h2h_scores(grp, tied_tids, team_list)
            
            # Ordenar por H2H (pts > GD > GF)
            def _h2h_key(t):
                tid = t[0]
                h = h2h[tid]
                return (-h["pts"], -(h["gf"] - h["ga"]), -h["gf"])
            
            tie_group.sort(key=_h2h_key)
            
            # Verificar si H2H resolvió completamente
            h2h_sorted = [h2h[t[0]] for t in tie_group]
            h2h_unique = set(
                (h["pts"], h["gf"] - h["ga"], h["gf"])
                for h in h2h_sorted
            )
            
            if len(h2h_unique) == len(tie_group):
                # H2H resolvió completamente
                resolved.extend(tie_group)
            else:
                # H2H no resolvió — queda fair play / sorteo
                print(f"\n  ⚠️  Empate no resoluble en Grupo {grp}:")
                for t in tie_group:
                    name = id_name.get(t[0], f"Team {t[0]}")
                    h = h2h[t[0]]
                    print(f"      {name} — PTS={t[1]} GD={t[2]} GF={t[3]} | H2H: {h['pts']}pts ({h['gf']}-{h['ga']})")
                print(f"\n  🔗 Revisá https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/standings")
                print(f"     y ajustá el orden manualmente.\n")
                print(f"  Ingresá el orden de estos {len(tie_group)} equipos (1=mejor, separados por coma):")
                for i, t in enumerate(tie_group):
                    print(f"    {i+1}. {id_name.get(t[0], f'Team {t[0]}')}")
                while True:
                    try:
                        inp = input("    Orden (ej: 2,1,3,4): ").strip()
                        indices = [int(x.strip()) for x in inp.split(",")]
                        if sorted(indices) == list(range(1, len(tie_group)+1)):
                            tie_group = [tie_group[i-1] for i in indices]
                            break
                        else:
                            print(f"    ❌ Debés ingresar números del 1 al {len(tie_group)} en algún orden")
                    except (ValueError, IndexError):
                        print(f"    ❌ Formato inválido. Usá números del 1 al {len(tie_group)} separados por coma")
                resolved.extend(tie_group)
        
        # Asignar ranks (manejar empates en PTS/GD/GF que H2H no separó del todo)
        # Si H2H asignó ranks diferentes, usarlos
        result = []
        for rank, (tid, pts, gd, gf) in enumerate(resolved, 1):
            result.append((tid, rank))
        return result

    # ── Build group results ──
    grupos_result = {}
    grupos_activos = set()
    
    for grp, tids in group_teams.items():
        has_finished = any(stats[(grp, tid)]["played"] > 0 for tid in tids)
        if has_finished:
            grupos_activos.add(grp)
        
        ranked = _sort_group(grp, tids, has_finished)
        
        equipos = {}
        for tid, rank in ranked:
            name = id_name.get(tid, f"Team {tid}")
            equipos[name] = rank
        grupos_result[grp] = equipos
    
    # Contar partidos terminados
    total_finished = sum(1 for m in gm if m.get("finished") == "TRUE" and m.get("type") == "group")
    print(f"  ⚽ Partidos de grupo terminados: {total_finished}/72")
    
    # ── Mejores terceros (solo grupos activos) usando MISMO motor FIFA ──
    terceros = []
    for grp_letra in sorted(grupos_result.keys()):
        # grupos_result ya tiene el orden FIFA completo (con H2H y pregunta manual)
        ranked = list(grupos_result[grp_letra].items())  # [(name, rank), ...]
        if len(ranked) >= 3:
            eq_name = ranked[2][0]  # 3° lugar (index 2)
            # Obtener stats directamente
            s = stats.get((grp_letra, None), {})
            # Buscar tid para este equipo
            tid = None
            for k, v in id_name.items():
                if v == eq_name:
                    tid = k
                    break
            if tid:
                ss = stats[(grp_letra, tid)]
                terceros.append((grp_letra, ss["pts"], ss["gf"] - ss["ga"], eq_name))
    
    # Top 8 terceros (usando FIFA: PTS > GD > GF, y si empata → H2H no aplica entre grupos)
    terceros.sort(key=lambda x: (-x[1], -x[2]))
    terceros_clasificados = {t[0] for t in terceros[:8]}
    
    # ── Llenar slots 16avos (solo grupos con ≥1 partido) ──
    ronda_16 = []
    for slot, pos, grp in SLOTS_16AVOS:
        equipo = ""
        if pos in (1, 2) and isinstance(grp, str) and grp in grupos_activos and grp in grupos_result:
            for eq, r in grupos_result[grp].items():
                if r == pos: equipo = eq; break
        elif isinstance(grp, list):
            # Mejores terceros: solo cuando TODOS los grupos están activos
            if len(grupos_activos) >= 12:
                for t_letra, t_pts, t_gd, t_name in terceros:
                    if t_letra in grp and t_letra in terceros_clasificados:
                        equipo = t_name
                        break
        ronda_16.append({"slot": slot, "equipo": equipo})
    
    # ── Rellenar KO desde partidos terminados ──
    def _find_match(mid, games_list):
        for g in games_list:
            if str(g.get("id")) == str(mid): return g
        return None
    
    def _winner(match):
        if not match or match.get("finished") != "TRUE": return ""
        hs = int(match.get("home_score",0) or 0)
        aw = int(match.get("away_score",0) or 0)
        if hs > aw: return id_name.get(str(match.get("home_team_id","")), "")
        if aw > hs: return id_name.get(str(match.get("away_team_id","")), "")
        return ""
    
    def _loser(match):
        if not match or match.get("finished") != "TRUE": return ""
        hs = int(match.get("home_score",0) or 0)
        aw = int(match.get("away_score",0) or 0)
        if hs < aw: return id_name.get(str(match.get("home_team_id","")), "")
        if aw < hs: return id_name.get(str(match.get("away_team_id","")), "")
        return ""
    
    # R16 (8avos): matches 89-96
    r8_winners = [_winner(_find_match(mid, gm)) for mid in range(89, 97)]
    ronda_8 = [{"equipo": w} for w in r8_winners if w]
    
    # QF: 97-100
    qf_winners = [_winner(_find_match(mid, gm)) for mid in range(97, 101)]
    ronda_4 = [{"equipo": w} for w in qf_winners if w]
    
    # SF: 101-102
    sf_winners = [_winner(_find_match(mid, gm)) for mid in (101, 102)]
    sf_losers = [_loser(_find_match(mid, gm)) for mid in (101, 102)]
    ronda_2 = [{"equipo": w} for w in sf_winners if w]
    
    # 3rd: 103
    m103 = _find_match(103, gm)
    tercero_e = _winner(m103)
    cuarto_e = _loser(m103)
    
    # Final: 104
    m104 = _find_match(104, gm)
    campeon_e = _winner(m104)
    segundo_e = _loser(m104)
    
    finales = {
        "campeon": campeon_e, "segundo": segundo_e,
        "tercero": tercero_e, "cuarto": cuarto_e,
    }
    
    # Validar si hay datos
    eq16 = sum(1 for e in ronda_16 if e["equipo"])
    if eq16 == 0:
        print("  ⚠️  Sin equipos en 16avos. ¿Grupos sin terminar?")
        return None
    
    print(f"  ⚽ 16avos: {eq16}/32 equipos asignados")
    print(f"  ⚽ 8avos: {len(ronda_8)}/16 | Cuartos: {len(ronda_4)}/8 | Semis: {len(ronda_2)}/4")
    print(f"  🏆 Campeón: {campeon_e or '—'}")
    
    # Construir stats para el frontend
    api_stats = {}
    for (grp, tid), s in stats.items():
        name = id_name.get(tid, f"Team {tid}")
        if grp not in api_stats:
            api_stats[grp] = {}
        api_stats[grp][name] = {"pts": s["pts"], "gf": s["gf"], "ga": s["ga"]}
    
    return {
        "_nota": f"Datos desde worldcup26.ir — {eq16}/32 equipos en 16avos",
        "_stats": api_stats,
        "grupos": grupos_result,
        "ronda_16avos": ronda_16,
        "ronda_8avos": ronda_8,
        "ronda_cuartos": ronda_4,
        "ronda_semifinales": ronda_2,
        "finales": finales,
    }

def validar_manual():
    if not RESULTADOS_FILE.exists():
        print(f"  ❌ No existe {RESULTADOS_FILE}"); return None
    with open(RESULTADOS_FILE, encoding="utf-8") as f:
        d = json.load(f)
    eq = sum(1 for e in d.get("ronda_16avos",[]) if e.get("equipo"))
    print(f"  ✅ Manual: {eq}/32 equipos en 16avos")
    return d

def main():
    modo = "auto"
    if "--api" in sys.argv: modo = "api"
    elif "--manual" in sys.argv: modo = "manual"
    print("📡 Obteniendo resultados del Mundial 2026...\n")
    datos = build_results_from_api() if modo in ("auto","api") else None
    if datos is None and modo in ("auto","manual"):
        print("📋 Usando datos manuales...")
        datos = validar_manual()
    if datos is None:
        print("\n❌ Sin resultados. Opciones:")
        print("   1. Editar data/resultados_reales.json")
        print("   2. Esperar partidos terminados")
        sys.exit(1)
    if modo != "manual":
        with open(RESULTADOS_FILE, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"  💾 Guardado en {RESULTADOS_FILE}")
    print("\n✅ Listo para calificar.py")

if __name__ == "__main__":
    main()
