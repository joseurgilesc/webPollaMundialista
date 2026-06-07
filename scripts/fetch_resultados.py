#!/usr/bin/env python3
"""
Obtiene resultados reales del Mundial 2026 desde la API gratuita worldcup26.ir.

Modo dual:
  - API (por defecto): consulta worldcup26.ir/get/games, /get/groups, /get/teams
  - Manual (--manual): usa el JSON local data/resultados_reales.json

Cuando el torneo esté en curso, la API devuelve scores en vivo y standings
actualizados. El script los convierte al formato que espera calificar.py.

Uso:
  python3 fetch_resultados.py           # API → actualiza resultados_reales.json
  python3 fetch_resultados.py --api     # solo API
  python3 fetch_resultados.py --manual  # solo validar JSON manual
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────

API_BASE = "https://worldcup26.ir"
RESULTADOS_FILE = Path("data/resultados_reales.json")

# ── Mapeo de labels API → códigos de slot ─────────────────────────

def label_a_slot(label: str) -> str:
    """
    Convierte un label de la API a nuestro código de slot.
    
    Ejemplos:
      "Winner Group E"       → "1E"
      "Runner-up Group A"    → "2A"  
      "3rd Group A/B/C/D/F"  → "3 ABCDF"
      "Winner Match 74"      → None (no es slot de 16avos)
    """
    label = label.strip()
    
    # Winner Group X → 1X
    if label.upper().startswith("WINNER GROUP"):
        grupo = label.split()[-1]
        return f"1{grupo}"
    
    # Runner-up Group X → 2X
    if label.upper().startswith("RUNNER-UP GROUP"):
        grupo = label.split()[-1]
        return f"2{grupo}"
    
    # 3rd Group A/B/C/D/F → 3 ABCDF
    if label.upper().startswith("3RD GROUP"):
        grupos = label.split("3rd Group")[-1].strip()
        # Quitar espacios y dividir por /
        letras = "".join(grupos.split("/")).strip()
        return f"3 {letras}"
    
    # Winner Match XX → no es slot (es para rondas posteriores)
    # Loser Match XX → no es slot
    return None


# ── API calls ──────────────────────────────────────────────────────

def _api_get(endpoint: str) -> dict | list:
    """Llama a worldcup26.ir y retorna los datos parseados."""
    url = f"{API_BASE}/{endpoint}"
    req = urllib.request.Request(url)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  ⚠️  HTTP {e.code} en {url}")
        return None
    except Exception as e:
        print(f"  ⚠️  Error en {url}: {e}")
        return None


def _api_get_teams() -> dict | None:
    """
    Obtiene los 48 equipos. Retorna {team_id: {name_en, fifa_code, group}}.
    """
    data = _api_get("get/teams")
    if not data:
        return None
    
    teams = data.get("teams", data) if isinstance(data, dict) else data
    if not isinstance(teams, list):
        return None
    
    team_map = {}
    for t in teams:
        tid = t.get("id", "")
        team_map[tid] = {
            "name": t.get("name_en", ""),
            "code": t.get("fifa_code", ""),
            "group": t.get("groups", ""),
        }
    
    return team_map


def _api_get_groups() -> dict | None:
    """
    Obtiene standings de grupos.
    Retorna {group_letter: {team_id: {pts, gf, ga, rank}}}.
    """
    data = _api_get("get/groups")
    if not data:
        return None
    
    groups_data = data.get("groups", data) if isinstance(data, dict) else data
    if not isinstance(groups_data, list):
        return None
    
    grupos = {}
    for g in groups_data:
        letra = g.get("name", "")
        equipos = {}
        for entry in sorted(g.get("teams", []), key=lambda e: -int(e.get("pts", 0))):
            tid = entry.get("team_id", "")
            equipos[tid] = {
                "pts": int(entry.get("pts", 0)),
                "gf": int(entry.get("gf", 0)),
                "ga": int(entry.get("ga", 0)),
            }
        # Asignar rank (1-4) por orden de pts, luego GD
        ranked = sorted(equipos.items(), key=lambda x: (-x[1]["pts"], -(x[1]["gf"] - x[1]["ga"])))
        for rank, (tid, info) in enumerate(ranked, 1):
            info["rank"] = rank
        grupos[letra] = dict(ranked)
    
    return grupos


def _api_get_matches() -> list | None:
    """Obtiene los 104 partidos."""
    data = _api_get("get/games")
    if not data:
        return None
    
    games = data.get("games", data) if isinstance(data, dict) else data
    return games if isinstance(games, list) else None


# ── Construir resultados desde API ─────────────────────────────────

def build_results_from_api() -> dict | None:
    """
    Construye el dict de resultados_reales.json desde los datos de la API.
    Retorna None si no se pudo obtener datos.
    """
    print("🌐 Consultando worldcup26.ir...")
    
    teams = _api_get_teams()
    groups = _api_get_groups()
    matches = _api_get_matches()
    
    if not teams:
        print("  ❌ No se pudieron obtener equipos")
        return None
    if not groups:
        print("  ❌ No se pudieron obtener grupos")
        return None
    if not matches:
        print("  ❌ No se pudieron obtener partidos")
        return None
    
    print(f"  ✅ {len(teams)} equipos, {len(groups)} grupos, {len(matches)} partidos")
    
    # ── Mapear grupos al formato de resultados_reales ──
    grupos_result = {}
    for letra, equipos_dict in groups.items():
        grupo_equipos = {}
        for tid, info in equipos_dict.items():
            nombre = teams.get(tid, {}).get("name", f"Team {tid}")
            grupo_equipos[nombre] = info.get("rank", 0)
        if grupo_equipos:
            grupos_result[letra] = grupo_equipos
    
    # ── Mapear R32 (16avos) ──
    r32_matches = [m for m in matches if m.get("type") == "r32"]
    
    ronda_16avos = []
    for m in sorted(r32_matches, key=lambda x: int(x.get("id", 0))):
        # Intentar obtener equipos reales (si ya están determinados)
        home_id = m.get("home_team_id", "0")
        away_id = m.get("away_team_id", "0")
        home_label = m.get("home_team_label", "")
        away_label = m.get("away_team_label", "")
        
        home_name = teams.get(home_id, {}).get("name", "") if home_id != "0" else ""
        away_name = teams.get(away_id, {}).get("name", "") if away_id != "0" else ""
        
        # Cada partido de R32 tiene 2 slots (home y away)
        home_slot = label_a_slot(home_label)
        away_slot = label_a_slot(away_label)
        
        if home_slot:
            ronda_16avos.append({
                "slot": home_slot,
                "equipo": home_name,
                "label_api": home_label,
            })
        if away_slot:
            ronda_16avos.append({
                "slot": away_slot,
                "equipo": away_name,
                "label_api": away_label,
            })
    
    # ── Construir rondas posteriores desde los partidos ──
    # R16 (#89-#96), QF (#97-#100), SF (#101-#102), 3rd (#103), Final (#104)
    
    def get_match_winners(match_ids: list, matches: list, teams: dict) -> list:
        """Obtiene los equipos ganadores de una lista de partidos."""
        winners = []
        for mid in match_ids:
            m = next((m for m in matches if m.get("id") == str(mid)), None)
            if not m:
                continue
            home_id = m.get("home_team_id", "0")
            away_id = m.get("away_team_id", "0")
            home_score = int(m.get("home_score", 0) or 0)
            away_score = int(m.get("away_score", 0) or 0)
            
            if home_id != "0" and away_id != "0" and home_score != away_score:
                # Partido jugado, hay ganador
                if home_score > away_score:
                    winners.append(teams.get(home_id, {}).get("name", ""))
                else:
                    winners.append(teams.get(away_id, {}).get("name", ""))
            elif home_id != "0" and away_id != "0" and home_score == away_score:
                # Empate (poco probable en knockout pero por si acaso)
                winners.append("")  # placeholder
            else:
                # Partido no jugado aún
                winners.append("")
        return winners
    
    # R16: matches 89-96
    r16_winners = get_match_winners(range(89, 97), matches, teams)
    ronda_8avos = [{"equipo": w} for w in r16_winners if w]
    
    # QF: matches 97-100
    qf_winners = get_match_winners(range(97, 101), matches, teams)
    ronda_cuartos = [{"equipo": w} for w in qf_winners if w]
    
    # SF: matches 101-102
    sf_winners = get_match_winners(range(101, 103), matches, teams)
    ronda_semis = [{"equipo": w} for w in sf_winners if w]
    
    # También necesitamos los perdedores de semis para 3er/4to puesto
    sf_losers = []
    for mid in [101, 102]:
        m = next((m for m in matches if m.get("id") == str(mid)), None)
        if not m:
            continue
        home_id = m.get("home_team_id", "0")
        away_id = m.get("away_team_id", "0")
        home_score = int(m.get("home_score", 0) or 0)
        away_score = int(m.get("away_score", 0) or 0)
        if home_id != "0" and away_id != "0" and home_score != away_score:
            if home_score < away_score:
                sf_losers.append(teams.get(home_id, {}).get("name", ""))
            else:
                sf_losers.append(teams.get(away_id, {}).get("name", ""))
    
    # 3rd place: match 103
    third_match = next((m for m in matches if m.get("id") == "103"), None)
    final_match = next((m for m in matches if m.get("id") == "104"), None)
    
    def get_match_winner(match, teams):
        if not match:
            return ""
        home_id = match.get("home_team_id", "0")
        away_id = match.get("away_team_id", "0")
        hs = int(match.get("home_score", 0) or 0)
        as_ = int(match.get("away_score", 0) or 0)
        if home_id != "0" and away_id != "0" and hs != as_:
            if hs > as_:
                return teams.get(home_id, {}).get("name", "")
            return teams.get(away_id, {}).get("name", "")
        return ""
    
    def get_match_loser(match, teams):
        if not match:
            return ""
        home_id = match.get("home_team_id", "0")
        away_id = match.get("away_team_id", "0")
        hs = int(match.get("home_score", 0) or 0)
        as_ = int(match.get("away_score", 0) or 0)
        if home_id != "0" and away_id != "0" and hs != as_:
            if hs < as_:
                return teams.get(home_id, {}).get("name", "")
            return teams.get(away_id, {}).get("name", "")
        return ""
    
    tercero = get_match_winner(third_match, teams)
    cuarto = get_match_loser(third_match, teams)
    campeon = get_match_winner(final_match, teams)
    segundo = get_match_loser(final_match, teams)
    
    # Si no hay datos de finales aún, las rondas vacías se llenarán manualmente
    
    # Determinar si hay suficientes datos para scoring
    equipos_en_16 = sum(1 for e in ronda_16avos if e.get("equipo"))
    
    if equipos_en_16 == 0:
        print(f"  ⚠️  El torneo aún no empezó: {len(ronda_16avos)} slots pero 0 equipos asignados")
        print(f"  📝 Usá el JSON manual mientras tanto")
        return None
    
    resultados = {
        "_nota": f"Datos desde worldcup26.ir — {equipos_en_16}/32 equipos en 16avos",
        "grupos": grupos_result,
        "ronda_16avos": ronda_16avos,
        "ronda_8avos": ronda_8avos,
        "ronda_cuartos": ronda_cuartos,
        "ronda_semifinales": ronda_semis,
        "finales": {
            "campeon": campeon,
            "segundo": segundo,
            "tercero": tercero,
            "cuarto": cuarto,
        },
    }
    
    return resultados


# ── Validación manual ─────────────────────────────────────────────

def validar_manual() -> dict | None:
    """Lee y valida el archivo JSON manual."""
    if not RESULTADOS_FILE.exists():
        print(f"  ❌ No existe {RESULTADOS_FILE}")
        return None
    
    with open(RESULTADOS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    
    errores = []
    
    if len(data.get("grupos", {})) != 12:
        errores.append(f"Se esperaban 12 grupos, hay {len(data.get('grupos', {}))}")
    
    r16 = data.get("ronda_16avos", [])
    llenos = sum(1 for e in r16 if e.get("equipo"))
    if llenos == 0:
        errores.append("ronda_16avos está vacía")
    
    if errores:
        print("  ⚠️  Validación manual:")
        for e in errores:
            print(f"     - {e}")
        return None
    
    print(f"  ✅ Datos manuales: {llenos}/32 equipos en 16avos")
    return data


# ── Main ───────────────────────────────────────────────────────────

def main():
    modo = "auto"
    if "--api" in sys.argv:
        modo = "api"
    elif "--manual" in sys.argv:
        modo = "manual"
    
    print("📡 Obteniendo resultados del Mundial 2026...")
    print()
    
    datos = None
    
    if modo in ("auto", "api"):
        datos = build_results_from_api()
    
    if datos is None and modo in ("auto", "manual"):
        print("📋 Usando datos manuales...")
        datos = validar_manual()
    
    if datos is None:
        print()
        print("❌ No se pudieron obtener resultados.")
        print("   El torneo aún no comenzó (11 de junio 2026).")
        print("   Opciones:")
        print("   1. Editar data/resultados_reales.json manualmente")
        print("   2. Esperar a que arranque el mundial para datos automáticos")
        sys.exit(1)
    
    # Si los datos vinieron de la API, guardarlos
    if modo != "manual":
        with open(RESULTADOS_FILE, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"  💾 Guardado en {RESULTADOS_FILE}")
    
    print()
    print("✅ Resultados listos para calificar.py")


if __name__ == "__main__":
    main()
