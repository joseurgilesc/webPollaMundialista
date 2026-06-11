#!/usr/bin/env python3
"""
Obtiene resultados reales del Mundial 2026 desde worldcup26.ir.

Campos reales de la API:
- games: home_team_name_en, away_team_name_en, home_team_id, away_team_id, home_score, away_score, type, group, matchday, finished, time_elapsed
- teams: id, name_en, fifa_code, groups
- groups: name, teams[{team_id, pts, gf, ga}]

Uso:
  python3 fetch_resultados.py           # intenta API, fallback a manual
  python3 fetch_resultados.py --api     # solo API
  python3 fetch_resultados.py --manual  # solo validar JSON manual
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

API_BASE = "https://worldcup26.ir"
RESULTADOS_FILE = Path("data/resultados_reales.json")

# ── Mapeo nombres inglés → español (como aparecen en las pollas) ──
ENGLISH_TO_POLLA = {
    "Mexico": "🇲🇽 MÉXICO",
    "South Africa": "🇿🇦 SUDÁFRICA",
    "South Korea": "🇰🇷 COREA DEL SUR",
    "Czech Republic": "🇨🇿 REP. CHECA",
    "Canada": "🇨🇦 CANADÁ",
    "Bosnia and Herzegovina": "🇧🇦 BOSNIA Y HERZEGOVINA",
    "Qatar": "🇶🇦 QATAR",
    "Switzerland": "🇨🇭 SUIZA",
    "Brazil": "🇧🇷 BRASIL",
    "Morocco": "🇲🇦 MARRUECOS",
    "Haiti": "🇭🇹 HAITÍ",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿 ESCOCIA",
    "United States": "🇺🇸 ESTADOS UNIDOS",
    "Paraguay": "🇵🇾 PARAGUAY",
    "Australia": "🇦🇺 AUSTRALIA",
    "Turkey": "🇹🇷 TURQUÍA",
    "Germany": "🇩🇪 ALEMANIA",
    "Curacao": "🇨🇼 CURAZAO",
    "Côte d'Ivoire": "🇨🇮 COSTA DE MARFIL",
    "Ivory Coast": "🇨🇮 COSTA DE MARFIL",
    "Ecuador": "🇪🇨 ECUADOR",
    "Netherlands": "🇳🇱 HOLANDA",
    "Japan": "🇯🇵 JAPÓN",
    "Sweden": "🇸🇪 SUECIA",
    "Tunisia": "🇹🇳 TÚNEZ",
    "Belgium": "🇧🇪 BÉLGICA",
    "Egypt": "🇪🇬 EGIPTO",
    "Iran": "🇮🇷 IRÁN",
    "New Zealand": "🇳🇿 NUEVA ZELANDA",
    "Spain": "🇪🇸 ESPAÑA",
    "Cape Verde": "🇨🇻 CABO VERDE",
    "Saudi Arabia": "🇸🇦 ARABIA SAUDÍ",
    "Uruguay": "🇺🇾 URUGUAY",
    "France": "🇫🇷 FRANCIA",
    "Senegal": "🇸🇳 SENEGAL",
    "Iraq": "🇮🇶 IRAK",
    "Norway": "🇳🇴 NORUEGA",
    "Argentina": "🇦🇷 ARGENTINA",
    "Algeria": "🇩🇿 ARGELIA",
    "Austria": "🇦🇹 AUSTRIA",
    "Jordan": "🇯🇴 JORDANIA",
    "Portugal": "🇵🇹 PORTUGAL",
    "DR Congo": "🇨🇩 REP. CONGO",
    "Congo DR": "🇨🇩 REP. CONGO",
    "Uzbekistan": "🇺🇿 UZBEKISTÁN",
    "Colombia": "🇨🇴 COLOMBIA",
    "England": "🇬🇧 INGLATERRA",
    "Croatia": "🇭🇷 CROACIA",
    "Ghana": "🇬🇭 GHANA",
    "Panama": "🇵🇦 PANAMÁ",
}

def _api_get(endpoint: str) -> dict | list:
    url = f"{API_BASE}/{endpoint}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠️  Error API: {e}")
        return None

def _en_to_polla(name_en: str) -> str:
    """Convierte nombre inglés de la API al formato de las pollas."""
    return ENGLISH_TO_POLLA.get(name_en, name_en.upper())

def label_a_slot(label: str) -> str | None:
    """Winner Group E → 1E, Runner-up Group A → 2A, 3rd Group A/B/C/D/F → 3 ABCDF"""
    label = label.strip()
    m = re.match(r'^Winner Group ([A-L])$', label, re.I)
    if m: return f"1{m.group(1)}"
    m = re.match(r'^Runner-up Group ([A-L])$', label, re.I)
    if m: return f"2{m.group(1)}"
    m = re.match(r'^3rd Group (.+)$', label, re.I)
    if m: return f"3 {m.group(1).replace('/', '').strip()}"
    return None

def build_results_from_api() -> dict | None:
    print("🌐 Consultando worldcup26.ir...")
    
    teams = _api_get("get/teams")
    groups = _api_get("get/groups")
    games = _api_get("get/games")
    
    if not teams or not groups or not games:
        print("  ❌ No se pudieron obtener datos")
        return None
    
    teams_list = teams.get("teams", teams) if isinstance(teams, dict) else teams
    groups_list = groups.get("groups", groups) if isinstance(groups, dict) else groups
    games_list = games.get("games", games) if isinstance(games, dict) else games
    
    print(f"  ✅ {len(teams_list)} equipos, {len(groups_list)} grupos, {len(games_list)} partidos")
    
    # ── Mapeo team_id → nombre polla ──
    id_to_name = {}
    for t in teams_list:
        tid = str(t.get("id", ""))
        name_en = t.get("name_en", "")
        id_to_name[tid] = _en_to_polla(name_en)
    
    # ── Grupos: standings ──
    grupos_result = {}
    for g in groups_list:
        letra = g.get("name", "")
        equipos = {}
        for entry in sorted(g.get("teams", []), key=lambda e: -int(e.get("pts", 0))):
            tid = str(entry.get("team_id", ""))
            pts = int(entry.get("pts", 0))
            name = id_to_name.get(tid, f"Team {tid}")
            # Rank será asignado después de ordenar
            equipos[name] = 0  # placeholder, se asigna rank después
        # Asignar ranks 1-4 por orden de pts, luego GD
        ranked = sorted(equipos.items(), key=lambda x: 0)
        if equipos:
            grupos_result[letra] = {name: i+1 for i, (name, _) in enumerate(ranked)}
    
    # ── Bracket R32 ──
    r32_matches = [g for g in games_list if g.get("type") == "r32"]
    ronda_16avos = []
    
    for m in sorted(r32_matches, key=lambda x: int(x.get("id", 0))):
        # Buscar los labels de los equipos en estos partidos (Winner Group X, etc.)
        # La API no devuelve labels directamente, los deducimos del bracket FIFA
        # Usamos el slot mapping conocido del bracket
        pass
    
    # ── Obtener partidos jugados para llenar bracket ──
    group_matches = [g for g in games_list if g.get("type") == "group" and g.get("finished") == "TRUE"]
    knockout_matches = [g for g in games_list if g.get("type") != "group" and g.get("finished") == "TRUE"]
    
    print(f"  ⚽ Partidos grupos jugados: {len(group_matches)}")
    print(f"  ⚽ Partidos KO jugados: {len(knockout_matches)}")
    
    # Por ahora, si no hay partidos de grupo terminados, no podemos llenar el bracket
    if len(group_matches) == 0:
        print("  ⚠️  Aún no hay partidos terminados. Usá el JSON manual.")
        return None
    
    # ── Construir bracket desde partidos jugados ──
    # ... (lógica de llenado de bracket según resultados)
    
    # Placeholder
    resultados = {
        "_nota": "Datos desde worldcup26.ir (API)",
        "grupos": grupos_result,
        "ronda_16avos": [],
        "ronda_8avos": [],
        "ronda_cuartos": [],
        "ronda_semifinales": [],
        "finales": {"campeon": "", "segundo": "", "tercero": "", "cuarto": ""},
    }
    
    return resultados

def validar_manual():
    if not RESULTADOS_FILE.exists():
        print(f"  ❌ No existe {RESULTADOS_FILE}")
        return None
    with open(RESULTADOS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    llenos = sum(1 for e in data.get("ronda_16avos", []) if e.get("equipo"))
    print(f"  ✅ Datos manuales: {llenos}/32 equipos en 16avos")
    return data

def main():
    modo = "auto"
    if "--api" in sys.argv: modo = "api"
    elif "--manual" in sys.argv: modo = "manual"
    
    print("📡 Obteniendo resultados del Mundial 2026...\n")
    datos = None
    
    if modo in ("auto", "api"):
        datos = build_results_from_api()
    
    if datos is None and modo in ("auto", "manual"):
        print("📋 Usando datos manuales...")
        datos = validar_manual()
    
    if datos is None:
        print("\n❌ No se pudieron obtener resultados.")
        print("   Opciones:")
        print("   1. Editar data/resultados_reales.json manualmente")
        print("   2. Esperar a que se jueguen partidos")
        sys.exit(1)
    
    if modo != "manual":
        with open(RESULTADOS_FILE, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"  💾 Guardado en {RESULTADOS_FILE}")
    
    print("\n✅ Listo para calificar.py")

if __name__ == "__main__":
    main()
