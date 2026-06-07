#!/usr/bin/env python3
"""
Motor de scoring para pollas mundialistas.

Compara cada polla contra los resultados reales y calcula puntajes
aplicando las reglas oficiales con deduplicación.

Uso: python3 calificar.py
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict

# ── Config ─────────────────────────────────────────────────────────

POLLAS_DIR = Path("data/pollas")
RESULTADOS_FILE = Path("data/resultados_reales.json")
SALIDA_FILE = Path("data/puntajes.json")


# ── Normalización de nombres de equipos ──────────────────────────

def normalizar_equipo(nombre: str) -> str:
    """
    Normaliza un nombre de equipo para comparación:
    - Quita banderas (emojis de bandera, caracteres no-word)
    - Convierte a mayúsculas
    - Quita espacios extra
    - Maneja variantes conocidas
    """
    if not nombre:
        return ""
    # Quitar emojis y caracteres especiales (banderas, etc.)
    nombre = re.sub(r'[^\w\sáéíóúñüÁÉÍÓÚÑÜ]', '', nombre, flags=re.UNICODE)
    # Normalizar espacios
    nombre = " ".join(nombre.split()).upper()
    # Variantes conocidas
    variantes = {
        "ESTADOS UNIDOS": "USA",
        "EEUU": "USA",
        "EUA": "USA",
        "REP CHECA": "REPUBLICA CHECA",
        "REP CONGO": "REPUBLICA DEL CONGO",
        "HOLANDA": "PAISES BAJOS",
        "NETHERLANDS": "PAISES BAJOS",
        "COSTA DE MARFIL": "COSTA DE MARFIL",
        "BOSNIA Y HERZEGOVINA": "BOSNIA",
        "ARABIA SAUDI": "ARABIA SAUDITA",
        "TURQUIA": "TURQUIA",
        "COREA DEL SUR": "COREA DEL SUR",
        "NUEVA ZELANDA": "NUEVA ZELANDA",
        "CABO VERDE": "CABO VERDE",
    }
    return variantes.get(nombre, nombre)


# ── Scoring ────────────────────────────────────────────────────────

def _valor_entrada_16avos(entry: dict, real_por_equipo: dict, real_por_slot: dict) -> int:
    """
    Calcula cuántos puntos daría una entrada de 16avos.
    2 = equipo correcto + slot correcto
    1 = equipo correcto, slot incorrecto
    0 = equipo no está en 16avos reales
    """
    eq = normalizar_equipo(entry.get("equipo", ""))
    slot = entry.get("slot", "")
    if not eq:
        return 0
    if eq not in real_por_equipo:
        return 0
    if slot and slot in real_por_slot and normalizar_equipo(real_por_slot[slot]) == eq:
        return 2
    return 1


def _deduplicar_mejor(lista: list, valor_func, *valor_args) -> list:
    """
    Elimina equipos duplicados, conservando la entrada que da MAYOR puntaje.
    Si hay empate, conserva la primera.
    """
    mejor_por_equipo = {}  # equipo -> (valor, entry)
    for entry in lista:
        equipo = entry.get("equipo", "")
        if not equipo:
            continue
        valor = valor_func(entry, *valor_args)
        if equipo not in mejor_por_equipo or valor > mejor_por_equipo[equipo][0]:
            mejor_por_equipo[equipo] = (valor, entry)
    
    # Reconstruir lista en orden original, pero con las mejores entradas
    resultado = []
    vistos = set()
    for entry in lista:
        equipo = entry.get("equipo", "")
        if not equipo or equipo in vistos:
            continue
        vistos.add(equipo)
        resultado.append(mejor_por_equipo[equipo][1])
    
    return resultado


def _deduplicar_primero(lista: list) -> list:
    """
    Elimina equipos duplicados, conservando la primera aparición.
    Para rondas donde todas las ocurrencias valen lo mismo (8avos, cuartos, semis).
    """
    vistos = set()
    resultado = []
    for entry in lista:
        equipo = entry.get("equipo", "")
        if equipo and equipo not in vistos:
            vistos.add(equipo)
            resultado.append(entry)
    return resultado


def _scorear_16avos(polla_entries: list, real_entries: list) -> tuple[int, dict]:
    """
    Scoring de 16avos:
    - 1 pt por equipo acertado (sin importar posición)
    - 1 pt extra si acierta slot (posición)
    - Equipos duplicados en la polla solo cuentan una vez
    
    Retorna (puntaje_total, detalle).
    """
    # Construir mapas: equipo -> slots reales
    real_por_equipo = defaultdict(list)
    real_por_slot = {}
    for e in real_entries:
        eq = normalizar_equipo(e.get("equipo", ""))
        slot = e.get("slot", "")
        if eq:
            real_por_equipo[eq].append(slot)
        if slot:
            real_por_slot[slot] = e.get("equipo", "")  # guardar original para mostrar
    
    # Deduplicar polla: conservar la entrada que da MÁS puntos
    polla_unicos = _deduplicar_mejor(polla_entries, _valor_entrada_16avos, real_por_equipo, real_por_slot)
    
    puntaje = 0
    detalle = {"aciertos_equipo": [], "aciertos_posicion": [], "errores": []}
    
    for entry in polla_unicos:
        eq = entry.get("equipo", "")
        slot = entry.get("slot", "")
        
        if not eq:
            continue
        
        # ¿Está el equipo en los 16avos reales?
        if eq in real_por_equipo:
            puntaje += 1
            detalle["aciertos_equipo"].append(eq)
            
            # ¿Está en el slot correcto?
            if slot and slot in real_por_slot and real_por_slot[slot] == eq:
                puntaje += 1
                detalle["aciertos_posicion"].append(f"{eq} @ {slot}")
            elif slot and slot in real_por_slot:
                detalle["errores"].append(f"{eq} en {slot} (real: {real_por_slot[slot]})")
        else:
            detalle["errores"].append(f"{eq} no clasificó a 16avos")
    
    return puntaje, detalle


def _scorear_ronda_simple(polla_entries: list, real_entries: list, puntos_por_acierto: int, nombre: str) -> tuple[int, dict]:
    """
    Scoring para 8avos, cuartos, semis:
    - X pts por equipo acertado (sin importar posición)
    - Deduplicación aplicada
    """
    polla_unicos = _deduplicar_primero(polla_entries)
    
    real_equipos = set()
    for e in real_entries:
        eq = normalizar_equipo(e.get("equipo", ""))
        if eq:
            real_equipos.add(eq)
    
    puntaje = 0
    detalle = {"aciertos": [], "errores": []}
    
    for entry in polla_unicos:
        eq = normalizar_equipo(entry.get("equipo", ""))
        if not eq:
            continue
        
        if eq in real_equipos:
            puntaje += puntos_por_acierto
            detalle["aciertos"].append(eq)
        else:
            detalle["errores"].append(f"{eq} no llegó a {nombre}")
    
    return puntaje, detalle


def _scorear_finales(polla_finales: dict, real_finales: dict) -> tuple[int, dict]:
    """
    Scoring de finales:
    - Campeón: 20 pts
    - Segundo: 11 pts
    - Tercero: 8 pts
    - Cuarto: 5 pts
    """
    PUNTOS = {"campeon": 20, "segundo": 11, "tercero": 8, "cuarto": 5}
    
    puntaje = 0
    detalle = {"aciertos": [], "errores": []}
    
    for puesto, pts in PUNTOS.items():
        predicho = normalizar_equipo(polla_finales.get(puesto, ""))
        real = normalizar_equipo(real_finales.get(puesto, ""))
        
        if not predicho:
            detalle["errores"].append(f"{puesto}: sin predicción")
            continue
        
        if predicho == real:
            puntaje += pts
            detalle["aciertos"].append(f"{puesto}: {predicho} (+{pts})")
        else:
            detalle["errores"].append(f"{puesto}: predijo {predicho}, real: {real} (0 pts)")
    
    return puntaje, detalle


# ── Scoring principal ──────────────────────────────────────────────

def _normalizar_datos_polla(data: dict) -> dict:
    """Normaliza nombres de equipos en todos los campos de una polla."""
    import copy
    data = copy.deepcopy(data)
    # Grupos
    for g, eqs in data.get("grupos", {}).items():
        data["grupos"][g] = {normalizar_equipo(k): v for k, v in eqs.items()}
    # Rondas
    for ronda in ["ronda_16avos", "ronda_8avos", "ronda_cuartos", "ronda_semifinales"]:
        for e in data.get(ronda, []):
            if "equipo" in e:
                e["equipo"] = normalizar_equipo(e["equipo"])
    # Finales
    for k in ["campeon", "segundo", "tercero", "cuarto"]:
        if k in data.get("finales", {}):
            data["finales"][k] = normalizar_equipo(data["finales"][k])
    return data


def calificar_polla(polla: dict, real: dict) -> dict:
    """
    Calcula el puntaje completo de una polla contra los resultados reales.
    Retorna dict con puntaje por ronda y total.
    """
    # Normalizar datos de la polla para comparación
    polla = _normalizar_datos_polla(polla)
    real = _normalizar_datos_polla(real)
    
    resultado = {
        "participante": polla.get("participante", "?"),
        "archivo": polla.get("archivo_original", "?"),
        "puntajes": {},
        "detalle": {},
    }
    
    total = 0
    
    # 16avos
    pts, det = _scorear_16avos(
        polla.get("ronda_16avos", []),
        real.get("ronda_16avos", [])
    )
    resultado["puntajes"]["16avos"] = pts
    resultado["detalle"]["16avos"] = det
    total += pts
    
    # 8avos
    pts, det = _scorear_ronda_simple(
        polla.get("ronda_8avos", []),
        real.get("ronda_8avos", []),
        2, "8avos"
    )
    resultado["puntajes"]["8avos"] = pts
    resultado["detalle"]["8avos"] = det
    total += pts
    
    # Cuartos
    pts, det = _scorear_ronda_simple(
        polla.get("ronda_cuartos", []),
        real.get("ronda_cuartos", []),
        3, "cuartos"
    )
    resultado["puntajes"]["cuartos"] = pts
    resultado["detalle"]["cuartos"] = det
    total += pts
    
    # Semifinales
    pts, det = _scorear_ronda_simple(
        polla.get("ronda_semifinales", []),
        real.get("ronda_semifinales", []),
        4, "semifinales"
    )
    resultado["puntajes"]["semifinales"] = pts
    resultado["detalle"]["semifinales"] = det
    total += pts
    
    # Finales
    pts, det = _scorear_finales(
        polla.get("finales", {}),
        real.get("finales", {})
    )
    resultado["puntajes"]["finales"] = pts
    resultado["detalle"]["finales"] = det
    total += pts
    
    resultado["puntajes"]["total"] = total
    
    return resultado


# ── CLI ────────────────────────────────────────────────────────────

def main():
    # Cargar resultados reales
    if not RESULTADOS_FILE.exists():
        print(f"❌ No se encontró {RESULTADOS_FILE}")
        print("   Creá el archivo con los resultados reales primero.")
        return
    
    with open(RESULTADOS_FILE, encoding="utf-8") as f:
        real = json.load(f)
    
    # Validar que haya datos
    vacios_16 = sum(1 for e in real.get("ronda_16avos", []) if e.get("equipo"))
    if vacios_16 == 0:
        print("⚠️  Resultados reales vacíos — todos los puntajes en 0.")
        print("   El mundial aún no comienza. Los puntajes se activarán cuando haya resultados.")
    else:
        print(f"📊 Resultados reales cargados: {vacios_16}/32 equipos en 16avos")
    print()
    
    # Cargar todas las pollas
    pollas = []
    for f in sorted(POLLAS_DIR.glob("*.json")):
        with open(f, encoding="utf-8") as fp:
            pollas.append(json.load(fp))
    
    if not pollas:
        print("❌ No se encontraron pollas en data/pollas/")
        return
    
    # Calificar
    resultados = []
    for polla in pollas:
        r = calificar_polla(polla, real)
        resultados.append(r)
    
    # Ordenar por puntaje total descendente
    resultados.sort(key=lambda r: r["puntajes"]["total"], reverse=True)
    
    # Asignar letras de polla por participante (A, B, C...)
    polla_letras = {}
    for r in resultados:
        nombre = r["participante"]
        if nombre not in polla_letras:
            polla_letras[nombre] = []
        polla_letras[nombre].append(r)
    for nombre, pollas in polla_letras.items():
        for idx, r in enumerate(pollas):
            r["polla_letra"] = chr(ord("A") + idx)
    
    # Mostrar leaderboard
    print(f"{'='*80}")
    print(f"  LEADERBOARD")
    print(f"{'='*80}")
    print(f"  {'#':<3} {'Participante':<22} {'Polla':<6} {'16avos':>6} {'8avos':>6} {'Cuart':>6} {'Semis':>6} {'Final':>6} {'TOTAL':>6}")
    print(f"  {'─'*80}")
    
    for i, r in enumerate(resultados, 1):
        p = r["puntajes"]
        nombre = r["participante"][:21]
        letra = r["polla_letra"]
        print(f"  {i:<3} {nombre:<22} {letra:<6} {p['16avos']:>6} {p['8avos']:>6} {p['cuartos']:>6} {p['semifinales']:>6} {p['finales']:>6} {p['total']:>6}")
    
    print(f"  {'─'*80}")
    print(f"  Máximo posible:              64     32     24     16     44    180")
    print()
    
    # Guardar resultados
    with open(SALIDA_FILE, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"💾 Puntajes guardados en {SALIDA_FILE}")


if __name__ == "__main__":
    main()
