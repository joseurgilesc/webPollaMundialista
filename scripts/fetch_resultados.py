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
    
    # ── Grupos: standings con rank real ──
    grupos_result = {}
    grupos_completos = set()  # solo grupos con todos los partidos jugados
    
    # Detectar qué grupos están completos
    for g in gl:
        letra = g.get("name","")
        matches = [m for m in gm if m.get("group") == letra and m.get("type") == "group"]
        finished = [m for m in matches if m.get("finished") == "TRUE"]
        if len(matches) == 6 and len(finished) == 6:  # 4 equipos = 6 partidos
            grupos_completos.add(letra)
    
    for g in gl:
        letra = g.get("name","")
        entries = g.get("teams",[])
        # Solo ordenar si el grupo está completo
        if letra in grupos_completos:
            ranked = sorted(entries, key=lambda e: (-int(e.get("pts",0)), -(int(e.get("gf",0))-int(e.get("ga",0)))))
            equipos = {}
            for rank, e in enumerate(ranked, 1):
                name = id_name.get(str(e.get("team_id","")), "?")
                equipos[name] = rank
        else:
            # Grupo no terminado: posiciones pendientes
            equipos = {id_name.get(str(e.get("team_id","")), "?"): 0 for e in entries}
        if equipos:
            grupos_result[letra] = equipos
    
    # ── Determinar mejores terceros ──
    terceros = []
    for g in gl:
        letra = g.get("name","")
        entries = sorted(g.get("teams",[]), key=lambda e: (-int(e.get("pts",0)), -(int(e.get("gf",0))-int(e.get("ga",0)))))
        if len(entries) >= 3:
            e3 = entries[2]
            terceros.append((letra, int(e3.get("pts",0)), int(e3.get("gf",0))-int(e3.get("ga",0)), id_name.get(str(e3.get("team_id","")), "?")))
    
    # Top 8 terceros
    terceros.sort(key=lambda x: (-x[1], -x[2]))
    terceros_clasificados = {t[0] for t in terceros[:8]}
    
    # ── Llenar slots 16avos (solo grupos completos) ──
    ronda_16 = []
    for slot, pos, grp in SLOTS_16AVOS:
        equipo = ""
        if pos == 1:
            if isinstance(grp, str) and grp in grupos_completos and grp in grupos_result:
                for eq, r in grupos_result[grp].items():
                    if r == 1: equipo = eq; break
        elif pos == 2:
            if isinstance(grp, str) and grp in grupos_completos and grp in grupos_result:
                for eq, r in grupos_result[grp].items():
                    if r == 2: equipo = eq; break
        else:
            # Mejor tercero: solo si TODOS los grupos candidatos están completos
            if isinstance(grp, list):
                if all(g in grupos_completos for g in grp):
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
    
    return {
        "_nota": f"Datos desde worldcup26.ir — {eq16}/32 equipos en 16avos",
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
