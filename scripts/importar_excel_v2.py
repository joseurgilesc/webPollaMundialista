#!/usr/bin/env python3
"""
Parser alternativo para pollas en formato horizontal (Fer, Seb, etc.)

Formato:
- Grupos: 12 grupos en columnas B-Y, filas 5-8
- Bracket: slots y equipos dispersos en columnas C-AA, filas 12-30
- Participante: D2

Uso: python3 importar_excel_v2.py <archivo.xlsx> [...]
"""

import json, os, re, sys
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError:
    print("Error: openpyxl no instalado. pip3 install openpyxl")
    sys.exit(1)

def limpiar(texto):
    return " ".join(str(texto).split()).strip() if texto else ""

def es_slot(texto):
    """Detecta código de llave: 1E, 2A, 3 ABCDF, 3 CEFHI, etc."""
    t = limpiar(texto).upper()
    return bool(re.match(r'^[123]\s*[A-L]+$', t))

def parsear_excel_v2(filepath):
    wb = load_workbook(filepath, data_only=True)
    ws = wb[wb.sheetnames[0]]
    
    # Construir grilla
    grilla = {}
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row or 50):
        for cell in row:
            if cell.value is not None:
                val = str(cell.value).strip()
                if val:
                    grilla[(cell.row, cell.column_letter)] = val
    
    # ── Participante ──
    participante = grilla.get((2, "D"), "Sin nombre")
    
    # ── Grupos (horizontal B-Y) ──
    grupos = {}
    # Row 4: "GRUPO A", "GRUPO B", ... every 2 columns from B to Y
    # Row 5-8: equipos y posiciones
    col_inicio = col_letra_a_numero("B")
    col_fin = col_letra_a_numero("Y")
    
    for col_idx in range(col_inicio, col_fin + 1, 2):  # B, D, F, ...
        col_equipo = chr(ord('A') + col_idx)      # columna del equipo
        col_pos = chr(ord('A') + col_idx + 1)     # columna de la posición
        
        # Buscar encabezado "GRUPO X" en fila 4
        encabezado = grilla.get((4, col_equipo), "")
        if not encabezado.upper().startswith("GRUPO"):
            continue
        
        letra = encabezado.replace("GRUPO", "").strip()
        if not letra or len(letra) > 2:
            continue
        
        equipos = {}
        for fila in range(5, 9):
            equipo = limpiar(grilla.get((fila, col_equipo), ""))
            pos_str = grilla.get((fila, col_pos), "")
            if not equipo:
                continue
            try:
                pos = int(float(pos_str))
            except (ValueError, TypeError):
                pos = None
            equipos[equipo] = pos
        
        if equipos:
            grupos[letra] = equipos
    
    # ── Bracket ──
    # Escanear filas 10-40 buscando códigos de slot y equipos cercanos
    ronda_16 = []
    ronda_8 = []
    ronda_4 = []
    ronda_2 = []
    
    # Mapeo de slots encontrados
    slots_encontrados = {}  # slot_code -> (fila, col)
    
    for fila in range(10, 40):
        for col_num in range(2, 27):  # B to AA
            col = chr(ord('A') + col_num)
            val = grilla.get((fila, col), "")
            if es_slot(val) and val not in slots_encontrados:
                slots_encontrados[val] = (fila, col)
    
    # Para cada slot, buscar el equipo más cercano (a la derecha o izquierda)
    for slot, (fila, col_slot) in slots_encontrados.items():
        col_idx = col_letra_a_numero(col_slot)
        equipo = ""
        
        # Buscar en celdas adyacentes (derecha, izquierda, debajo)
        for offset_col in [1, -1, 2, -2]:
            col_vecina = chr(ord('A') + col_idx + offset_col)
            val = grilla.get((fila, col_vecina), "")
            if val and not es_slot(val) and not val.upper() in ("CUARTOS", "8AVOS", "16AVOS", "SEMIFINALES", "FINAL", "MEJORES TERCEROS"):
                # Verificar que no sea un label de partido (M74, M89, etc.)
                if not re.match(r'^M\d{2,3}', val) and not re.match(r'^\d+AVOS', val, re.I):
                    equipo = limpiar(val)
                    break
        
        if equipo:
            ronda_16.append({"slot": slot, "equipo": equipo})
    
    # ── 8avos ──
    # Buscar en columnas F y T
    for fila in range(12, 35):
        for col in ("F", "T"):
            val = grilla.get((fila, col), "")
            if val and not es_slot(val) and not val.upper() in ("CUARTOS", "8AVOS", "16AVOS", "SEMIFINALES", "FINAL"):
                if not re.match(r'^M\d{2,3}', val):
                    ronda_8.append({"equipo": limpiar(val)})
    
    # ── Cuartos ──
    for fila in range(13, 30):
        for col in ("H", "R"):
            val = grilla.get((fila, col), "")
            if val and not es_slot(val) and not val.upper() in ("CUARTOS", "8AVOS", "16AVOS", "SEMIFINALES", "FINAL"):
                if not re.match(r'^M\d{2,3}', val):
                    ronda_4.append({"equipo": limpiar(val)})
    
    # ── Semifinales ──
    # Buscar columnas típicas: K, P, etc.
    for fila in range(15, 35):
        for col in ("K", "P", "I", "S"):
            val = grilla.get((fila, col), "")
            if val and not es_slot(val) and not val.upper() in ("CUARTOS", "8AVOS", "16AVOS", "SEMIFINALES", "FINAL"):
                if not re.match(r'^M\d{2,3}', val):
                    eq = limpiar(val)
                    if eq and eq not in [e["equipo"] for e in ronda_2] and eq not in [e["equipo"] for e in ronda_4]:
                        ronda_2.append({"equipo": eq})
    
    # Limitar a cantidades correctas
    ronda_8 = ronda_8[:16]
    ronda_4 = ronda_4[:8]
    ronda_2 = ronda_2[:4]
    
    # ── Finales: no se pueden deducir automáticamente ──
    finales = {"campeon": None, "segundo": None, "tercero": None, "cuarto": None}
    
    # ── Validar ──
    errores = []
    if len(grupos) != 12:
        errores.append(f"Se encontraron {len(grupos)} grupos, se esperaban 12")
    
    equipos_16 = [e["equipo"] for e in ronda_16 if e["equipo"]]
    if len(equipos_16) < 10:
        errores.append(f"16avos: solo {len(equipos_16)} equipos encontrados (puede que el formato no coincida)")
    
    return {
        "archivo_original": os.path.basename(filepath),
        "participante": limpiar(participante),
        "grupos": grupos,
        "ronda_16avos": ronda_16,
        "ronda_8avos": ronda_8,
        "ronda_cuartos": ronda_4,
        "ronda_semifinales": ronda_2,
        "finales": finales,
        "errores": errores,
    }

def col_letra_a_numero(col):
    n = 0
    for c in col.upper():
        n = n * 26 + (ord(c) - ord('A') + 1)
    return n - 1

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 importar_excel_v2.py <archivo.xlsx> [...]")
        sys.exit(1)
    
    salida_dir = Path("data/pollas")
    salida_dir.mkdir(parents=True, exist_ok=True)
    
    for fp in sys.argv[1:]:
        if not os.path.exists(fp):
            print(f"⚠️  No existe: {fp}")
            continue
        print(f"\n{'='*60}")
        print(f"Parseando (v2): {fp}")
        
        try:
            datos = parsear_excel_v2(fp)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback; traceback.print_exc()
            continue
        
        print(f"  Participante: {datos['participante']}")
        print(f"  Grupos: {len(datos['grupos'])}")
        print(f"  16avos: {len(datos['ronda_16avos'])} slots")
        equipos = sum(1 for e in datos['ronda_16avos'] if e['equipo'])
        print(f"  8avos: {len(datos['ronda_8avos'])} equipos")
        print(f"  Cuartos: {len(datos['ronda_cuartos'])} equipos")
        print(f"  Semis: {len(datos['ronda_semifinales'])} equipos")
        
        if datos["errores"]:
            print(f"\n  ⚠️  Errores:")
            for e in datos["errores"]:
                print(f"     - {e}")
        else:
            print(f"  ✅ Sin errores")
        
        nombre = Path(fp).stem.lower().replace(" ", "_")
        with open(salida_dir / f"{nombre}.json", "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"  💾 {salida_dir / f'{nombre}.json'}")

if __name__ == "__main__":
    main()
