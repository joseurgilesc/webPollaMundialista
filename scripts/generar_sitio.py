#!/usr/bin/env python3
"""
Genera el sitio web estático para la Polla Mundialista 2026.

Genera dos páginas:
  - docs/index.html  → vista pública (leaderboard, gráficos)
  - docs/admin.html  → vista admin (pagos, transcripción PDF/imágenes)

Uso: python3 generar_sitio.py
"""

import json
from pathlib import Path
from datetime import datetime

PUNTAJES_FILE = Path("data/puntajes.json")
PARTICIPANTES_FILE = Path("data/participantes.json")
POLLAS_DIR = Path("data/pollas")
SALIDA_PUBLIC = Path("docs/index.html")
SALIDA_ADMIN = Path("docs/admin.html")

MAX_PUNTOS = {"16avos": 64, "8avos": 32, "cuartos": 24, "semifinales": 16, "finales": 44, "total": 180}
ADMIN_PASSWORD = "pollon2026"

# ── Colores oficiales Mundial 2026 ──
# FIFA navy, gold, teal sobre fondo blanco
COLORS = {
    "navy": "#0f1f4d",
    "gold": "#e8a817",
    "teal": "#0096c7",
    "bg": "#ffffff",
    "card": "#ffffff",
    "card_border": "#e2e8f0",
    "text": "#0f172a",
    "muted": "#64748b",
    "green": "#16a34a",
    "red": "#dc2626",
    "shadow": "0 4px 24px rgba(0,0,0,0.06)",
    "radius": "16px",
}

def calcular_acumulado(participantes: dict) -> int:
    costo = participantes.get("costo_por_polla", 10)
    return sum(p.get("pollas", 1) for p in participantes.get("participantes", []) if p.get("pago")) * costo

def css_comun() -> str:
    return f"""
:root {{
  --navy: {COLORS['navy']};
  --gold: {COLORS['gold']};
  --teal: {COLORS['teal']};
  --bg: {COLORS['bg']};
  --card: {COLORS['card']};
  --card-border: {COLORS['card_border']};
  --text: {COLORS['text']};
  --muted: {COLORS['muted']};
  --green: {COLORS['green']};
  --red: {COLORS['red']};
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: linear-gradient(180deg, #f0f4f8 0%, #ffffff 100%);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.5;
}}

/* Top bar */
.topbar {{
  background: linear-gradient(135deg, var(--navy), #1a3a6e);
  color: white;
  padding: 10px 0;
  text-align: center;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}}

.app {{ max-width: 960px; margin: 0 auto; padding: 24px 16px; }}

/* Header */
.header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  flex-wrap: wrap;
  gap: 12px;
}}
.header h1 {{
  font-size: clamp(24px, 5vw, 36px);
  font-weight: 800;
  letter-spacing: -0.5px;
  color: var(--navy);
}}
.header h1 .accent {{ color: var(--teal); }}
.header .badge {{
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  background: rgba(0, 150, 199, 0.1);
  color: var(--teal);
  border: 1px solid rgba(0, 150, 199, 0.3);
}}

/* Card */
.card {{
  background: var(--card);
  border: 1px solid var(--card-border);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: {COLORS['shadow']};
  margin-bottom: 20px;
}}

/* Grid */
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; margin-bottom: 20px; }}
.stat-card {{ text-align: center; }}
.stat-num {{ font-size: 1.8rem; font-weight: 800; color: var(--navy); }}
.stat-num.gold {{ color: var(--gold); }}
.stat-label {{ font-size: 0.75rem; color: var(--muted); margin-top: 2px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }}

/* Acumulado */
.acumulado {{ display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }}
.acumulado .icon {{ font-size: 2.5rem; }}
.acumulado .monto {{ font-size: 2.5rem; font-weight: 800; color: var(--gold); }}
.acumulado .info {{ font-size: 0.85rem; color: var(--muted); }}

/* Table */
.table-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
th {{
  padding: 12px 10px;
  text-align: center;
  color: var(--muted);
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-bottom: 2px solid var(--card-border);
  white-space: nowrap;
}}
th:first-child, td:first-child {{ text-align: left; padding-left: 16px; }}
td {{
  padding: 12px 10px;
  text-align: center;
  border-bottom: 1px solid #f1f5f9;
  white-space: nowrap;
}}
tr:hover td {{ background: #f8fafc; }}
.rank {{ font-weight: 700; width: 40px; }}
.nombre {{ text-align: left; font-weight: 600; }}
.polla-tag {{
  display: inline-block;
  background: var(--navy);
  color: white;
  font-size: 0.6rem;
  padding: 2px 7px;
  border-radius: 3px;
  margin-left: 6px;
  font-weight: 700;
}}
.total {{ font-weight: 800; font-size: 1.05rem; color: var(--gold); }}
.top1 td {{ background: linear-gradient(90deg, rgba(232,168,23,0.12) 0%, rgba(232,168,23,0.04) 100%); border-left: 3px solid var(--gold); }}
.top2 td {{ background: rgba(180,180,190,0.06); border-left: 3px solid #a0a0b0; }}
.top3 td {{ background: rgba(180,140,100,0.05); border-left: 3px solid #b8846e; }}
.medal {{ display: inline-block; width: 22px; text-align: center; font-size: 1.1rem; }}
.max-row td {{ color: var(--muted); font-size: 0.7rem; border-bottom: none; }}

/* Chart */
.chart-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }}
.chart-label {{ width: 110px; font-size: 0.75rem; text-align: right; color: var(--muted); flex-shrink: 0; font-weight: 600; }}
.chart-bars {{ flex: 1; display: flex; gap: 2px; height: 22px; border-radius: 5px; overflow: hidden; }}
.chart-bar {{ height: 100%; transition: width 0.6s ease; }}
.c16 {{ background: var(--teal); }} .c8 {{ background: var(--navy); }} .c4 {{ background: #7c3aed; }}
.c2 {{ background: #db2777; }} .cf {{ background: var(--gold); }}
.chart-total {{ width: 40px; font-size: 0.8rem; font-weight: 800; text-align: right; color: var(--navy); flex-shrink: 0; }}

/* Buttons */
.btn {{
  border: none;
  border-radius: 999px;
  padding: 10px 22px;
  background: var(--navy);
  color: white;
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}}
.btn:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(15, 31, 77, 0.3); }}
.btn-sm {{ padding: 7px 16px; font-size: 0.78rem; }}
.btn-outline {{ background: white; color: var(--navy); border: 2px solid var(--navy); }}
.btn-outline:hover {{ background: var(--navy); color: white; }}
.btn-green {{ background: var(--green); }}
.btn-red {{ background: var(--red); }}

/* Status */
.status {{
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
}}
.status.pagado {{ background: rgba(22, 163, 74, 0.1); color: var(--green); }}
.status.pendiente {{ background: rgba(220, 38, 38, 0.1); color: var(--red); }}

/* Toggle */
.toggle {{ position: relative; display: inline-block; width: 46px; height: 26px; }}
.toggle input {{ opacity: 0; width: 0; height: 0; }}
.toggle .slider {{
  position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
  background: #cbd5e1; border-radius: 26px; transition: 0.3s;
}}
.toggle .slider:before {{
  position: absolute; content: ""; height: 20px; width: 20px;
  left: 3px; bottom: 3px; background: white; border-radius: 50%; transition: 0.3s;
}}
.toggle input:checked + .slider {{ background: var(--green); }}
.toggle input:checked + .slider:before {{ transform: translateX(20px); }}

/* Forms */
input, textarea, select {{
  background: white;
  border: 2px solid var(--card-border);
  border-radius: 10px;
  padding: 10px 14px;
  color: var(--text);
  font-size: 0.88rem;
  font-family: inherit;
  width: 100%;
  transition: border-color 0.2s;
}}
input:focus, textarea:focus {{ outline: none; border-color: var(--teal); }}
label {{ display: block; font-size: 0.8rem; color: var(--muted); margin-bottom: 4px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }}

/* Form layout mejorado */
.slot-input {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid #f1f5f9;
}}
.slot-input .slot-code {{
  width: 90px;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--navy);
  flex-shrink: 0;
  font-family: 'SF Mono', 'Fira Code', monospace;
}}
.slot-input input {{
  flex: 1;
  max-width: 280px;
  font-size: 0.82rem;
  padding: 8px 12px;
}}

/* Pending files list */
.file-list {{ display: flex; flex-direction: column; gap: 6px; }}
.file-item {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 0.82rem;
}}
.file-item .file-name {{ font-weight: 600; color: var(--navy); }}
.file-item .file-badge {{
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
}}
.file-badge.pdf {{ background: rgba(220, 38, 38, 0.1); color: var(--red); }}
.file-badge.jpg {{ background: rgba(0, 150, 199, 0.1); color: var(--teal); }}
.file-badge.xlsx {{ background: rgba(22, 163, 74, 0.1); color: var(--green); }}

/* Toast */
.toast {{
  position: fixed; bottom: 24px; right: 24px;
  background: var(--navy); color: white; padding: 14px 24px;
  border-radius: 12px; font-weight: 600; font-size: 0.85rem;
  opacity: 0; transition: opacity 0.3s; z-index: 100;
}}
.toast.show {{ opacity: 1; }}

/* Lock */
.admin-locked {{ display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 80vh; gap: 16px; }}
.admin-locked input {{ max-width: 280px; text-align: center; font-size: 1.1rem; }}
.admin-locked h1 {{ color: var(--navy); }}

.hidden {{ display: none !important; }}
.form-group {{ margin-bottom: 16px; }}

/* Bracket sides */
.bracket-side {{
  margin-bottom: 12px;
}}
.bracket-side h4 {{
  color: var(--navy);
  font-size: 0.78rem;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--card-border);
}}

/* Footer */
footer {{ text-align: center; padding: 24px; color: var(--muted); font-size: 0.7rem; }}

@media (max-width: 600px) {{
  .app {{ padding: 12px 8px; }}
  .card {{ padding: 16px; border-radius: 12px; }}
  .header {{ flex-direction: column; align-items: flex-start; }}
  .header h1 {{ font-size: 22px; }}
  .chart-label {{ width: 70px; font-size: 0.65rem; }}
  table {{ font-size: 0.72rem; }}
  th, td {{ padding: 8px 4px; }}
  .slot-input .slot-code {{ width: 65px; font-size: 0.65rem; }}
}}
"""

def generar_publica(puntajes: list, participantes: dict) -> str:
    acumulado = calcular_acumulado(participantes)
    total_participantes = len(participantes.get("participantes", []))
    total_pollas = sum(p.get("pollas", 1) for p in participantes.get("participantes", []))
    
    # Contar pollas por participante (para decidir si mostrar letra)
    pollas_por_nombre = {}
    for r in puntajes:
        n = r["participante"]
        pollas_por_nombre[n] = pollas_por_nombre.get(n, 0) + 1
    
    filas = ""
    for i, r in enumerate(puntajes):
        p = r["puntajes"]
        nombre = r["participante"]
        letra = r.get("polla_letra", "A")
        mostrar_letra = pollas_por_nombre.get(nombre, 1) > 1
        medalla = {0: "🥇", 1: "🥈", 2: "🥉"}.get(i, "")
        clase = {0: "top1", 1: "top2", 2: "top3"}.get(i, "")
        tag_html = f'<span class="polla-tag">{letra}</span>' if mostrar_letra else ""
        
        filas += f"""<tr class="{clase}">
          <td class="rank">{medalla} {i+1}</td>
          <td class="nombre">{nombre}{tag_html}</td>
          <td>{p["16avos"]}</td><td>{p["8avos"]}</td><td>{p["cuartos"]}</td>
          <td>{p["semifinales"]}</td><td>{p["finales"]}</td>
          <td class="total">{p["total"]}</td></tr>"""
    
    # Fila de máximos
    filas += f"""<tr class="max-row">
      <td></td><td style="text-align:left;">Máximo posible</td>
      <td>64</td><td>32</td><td>24</td><td>16</td><td>44</td><td class="total">180</td></tr>"""
    
    barras_data = json.dumps([
        {"nombre": r["participante"][:12], "letra": r.get("polla_letra", "A"),
         "r16": r["puntajes"]["16avos"], "r8": r["puntajes"]["8avos"],
         "r4": r["puntajes"]["cuartos"], "r2": r["puntajes"]["semifinales"],
         "rf": r["puntajes"]["finales"]} for r in puntajes
    ])
    
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Polla Mundialista 2026</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{css_comun()}</style>
</head>
<body>

<div class="topbar">🇲🇽 MÉXICO · 🇨🇦 CANADÁ · 🇺🇸 ESTADOS UNIDOS — FIFA World Cup 2026™</div>

<div class="app">

  <header class="header">
    <div>
      <h1>⚽ Polla <span class="accent">Mundialista</span> 2026</h1>
      <div style="color:var(--muted);font-size:0.8rem;">Leaderboard en tiempo real</div>
    </div>
    <div class="badge">🔥 EN VIVO</div>
  </header>

  <div class="card acumulado">
    <div class="icon">💰</div>
    <div>
      <div class="stat-label" style="margin-bottom:2px;">ACUMULADO</div>
      <div class="monto">${acumulado:,}</div>
    </div>
    <div class="info" style="margin-left:auto;">
      {total_pollas} pollas registradas<br>
      ${participantes.get("costo_por_polla", 10)} c/u
    </div>
  </div>

  <div class="grid">
    <div class="card stat-card">
      <div class="stat-num">{total_participantes}</div>
      <div class="stat-label">Participantes</div>
    </div>
    <div class="card stat-card">
      <div class="stat-num">{total_pollas}</div>
      <div class="stat-label">Pollas</div>
    </div>
    <div class="card stat-card">
      <div class="stat-num gold">180</div>
      <div class="stat-label">Pts máximos</div>
    </div>
    <div class="card stat-card">
      <div class="stat-num gold">{puntajes[0]["puntajes"]["total"] if puntajes else 0}</div>
      <div class="stat-label">Líder</div>
    </div>
  </div>

  <div class="card">
    <h3 style="color:var(--navy);margin-bottom:16px;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.06em;">🏆 Leaderboard</h3>
    <div class="table-wrap"><table>
      <thead><tr><th>#</th><th>Participante</th><th>16avos</th><th>8avos</th><th>Cuartos</th><th>Semis</th><th>Final</th><th>Total</th></tr></thead>
      <tbody>{filas}</tbody>
    </table></div>
  </div>

  <div class="card">
    <h3 style="color:var(--navy);margin-bottom:16px;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.06em;">📊 Puntos por ronda</h3>
    <div id="chart"></div>
  </div>

</div>

<footer>Actualizado: {fecha} · Puntajes recalculados automáticamente</footer>

<script>
const D={barras_data};
const R=['r16','r8','r4','r2','rf'];
const C=document.getElementById('chart');
D.forEach(d=>{{
  const r=document.createElement('div');r.className='chart-row';
  r.innerHTML='<div class="chart-label">'+d.nombre+' '+d.letra+'</div>'+
    '<div class="chart-bars">'+R.map((k,i)=>'<div class="chart-bar c'+['16','8','4','2','f'][i]+'" style="width:'+(d[k]/180*100)+'%" title="'+['16avos','8avos','Cuartos','Semis','Final'][i]+': '+d[k]+' pts"></div>').join('')+'</div>'+
    '<div class="chart-total">'+R.reduce((s,k)=>s+d[k],0)+'</div>';
  C.appendChild(r);
}});
</script>
</body>
</html>"""

def generar_admin(participantes: dict) -> str:
    costo = participantes.get("costo_por_polla", 10)
    
    # ── Detectar archivos pendientes ──
    pendientes = []
    
    # PDFs e imágenes en pendientes/
    pendientes_dir = Path("pendientes")
    if pendientes_dir.exists():
        for f in sorted(pendientes_dir.iterdir()):
            if f.suffix.lower() in ('.pdf', '.jpg', '.jpeg', '.png'):
                pendientes.append({"nombre": f.name, "tipo": f.suffix.lower().replace('.', '')})
    
    # Excels no procesados aún
    excel_dir = Path("data/excel")
    pollas_dir = Path("data/pollas")
    if excel_dir.exists():
        procesados = set()
        if pollas_dir.exists():
            for jf in pollas_dir.glob("*.json"):
                procesados.add(jf.stem.replace("polla_", "").replace("_", " "))
        for xf in sorted(excel_dir.glob("*.xlsx")):
            if xf.name.startswith("~$"):
                continue
            nombre_base = xf.stem.lower().replace("_", " ")
            if nombre_base not in procesados:
                pendientes.append({"nombre": f"[Excel] {xf.name}", "tipo": "xlsx"})
    
    pendientes_json = json.dumps(pendientes)
    partes_json = json.dumps(participantes.get("participantes", []))
    
    # ── Equipos por grupo ──
    GRUPOS_EQUIPOS = {
        "A": ["🇲🇽 México", "🇿🇦 Sudáfrica", "🇰🇷 Corea del Sur", "🇨🇿 Rep. Checa"],
        "B": ["🇨🇦 Canadá", "🇧🇦 Bosnia y Herzegovina", "🇶🇦 Qatar", "🇨🇭 Suiza"],
        "C": ["🇧🇷 Brasil", "🇲🇦 Marruecos", "🇭🇹 Haití", "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Escocia"],
        "D": ["🇺🇸 Estados Unidos", "🇵🇾 Paraguay", "🇦🇺 Australia", "🇹🇷 Turquía"],
        "E": ["🇩🇪 Alemania", "🇨🇼 Curazao", "🇨🇮 Costa de Marfil", "🇪🇨 Ecuador"],
        "F": ["🇳🇱 Holanda", "🇯🇵 Japón", "🇸🇪 Suecia", "🇹🇳 Túnez"],
        "G": ["🇧🇪 Bélgica", "🇪🇬 Egipto", "🇮🇷 Irán", "🇳🇿 Nueva Zelanda"],
        "H": ["🇪🇸 España", "🇨🇻 Cabo Verde", "🇸🇦 Arabia Saudí", "🇺🇾 Uruguay"],
        "I": ["🇫🇷 Francia", "🇸🇳 Senegal", "🇮🇶 Irak", "🇳🇴 Noruega"],
        "J": ["🇦🇷 Argentina", "🇩🇿 Argelia", "🇦🇹 Austria", "🇯🇴 Jordania"],
        "K": ["🇵🇹 Portugal", "🇨🇩 Rep. Congo", "🇺🇿 Uzbekistán", "🇨🇴 Colombia"],
        "L": ["🇬🇧 Inglaterra", "🇭🇷 Croacia", "🇬🇭 Ghana", "🇵🇦 Panamá"],
    }
    TODOS_EQUIPOS = [e for eqs in GRUPOS_EQUIPOS.values() for e in eqs]
    
    # Generar datalists: uno por grupo + uno general
    datalists_html = "\n".join(
        f'<datalist id="g-{letra}">' + "".join(f'<option value="{e}">' for e in eqs) + '</datalist>'
        for letra, eqs in GRUPOS_EQUIPOS.items()
    )
    datalists_html += f'\n<datalist id="teams-all">' + "".join(f'<option value="{e}">' for e in TODOS_EQUIPOS) + '</datalist>'
    equipos_json = json.dumps(TODOS_EQUIPOS)
    grupos_equipos_json = json.dumps(GRUPOS_EQUIPOS)
    
    # Función para determinar el datalist según el código de slot
    import re
    def slot_datalist(slot_code: str) -> str:
        """Retorna el id del datalist apropiado para un slot."""
        # "1A", "2B" → grupo específico
        m = re.match(r'^[12]([A-L])$', slot_code.strip())
        if m:
            return f"g-{m.group(1)}"
        # "3 ABCDF" → todos los equipos de esos grupos
        if slot_code.strip().startswith("3 "):
            return "teams-all"
        return "teams-all"
    
    # Slots con su datalist
    slots_izq = ["1E","3 ABCDF","1I","3 CDFGH","2A","2B","1F","2C","2K","2L","1H","2J","1D","3 BEFIJ","1G","3 AEFHIJ"]
    slots_der = ["1C","2F","2E","2I","1A","3 CEFHI","1L","3 EHIJK","1J","2H","2D","2G","1B","3 EFGIJ","1K","3 DEIJL"]
    
    def slots_html(slots, prefix, start_idx):
        return "\n".join(
            f'<div class="slot-input"><span class="slot-code">{s}</span><input type="text" id="{prefix}{start_idx+i}" placeholder="Equipo" list="{slot_datalist(s)}" autocomplete="off"></div>'
            for i, s in enumerate(slots)
        )
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Admin — Polla Mundialista 2026</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
{css_comun()}
.section-title {{
  color: var(--navy);
  font-size: 0.8rem;
  margin: 20px 0 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--card-border);
}}
</style>
</head>
<body>

<div id="lockScreen" class="admin-locked">
  <h1>🔒</h1>
  <h2 style="color:var(--navy);">Admin — Polla 2026</h2>
  <input type="password" id="pwdInput" placeholder="Contraseña" autofocus>
  <button class="btn" onclick="unlock()">Entrar</button>
  <div id="lockError" style="color:var(--red);font-size:0.8rem;display:none;margin-top:8px;">Contraseña incorrecta</div>
</div>

<div id="adminContent" class="app hidden">

  <header class="header">
    <div>
      <h1>⚙️ Admin <span class="accent">Polla 2026</span></h1>
      <div style="color:var(--muted);font-size:0.8rem;">Gestión de pagos · Transcripción · Resultados</div>
    </div>
    <button class="btn btn-outline btn-sm" onclick="location.reload()">🔒 Salir</button>
  </header>

  <!-- Archivos pendientes -->
  <div class="card">
    <h3 style="color:var(--navy);margin-bottom:8px;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.06em;">📂 Archivos pendientes ({len(pendientes)})</h3>
    <div class="file-list" id="pendingList"></div>
    <div style="font-size:0.7rem;color:var(--muted);margin-top:8px;">Seleccioná uno y transcribilo abajo. Después movelo a <code>pendientes/procesados/</code></div>
  </div>

  <!-- Transcripción -->
  <div class="card">
    <h3 style="color:var(--navy);margin-bottom:16px;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.06em;">📋 Transcribir Polla</h3>
    
    <div class="form-group">
      <label>Seleccionar archivo pendiente</label>
      <select id="txArchivo" onchange="fillNombre(this)" style="max-width:400px;">
        <option value="">— Elegir —</option>
        {"".join(f'<option value="{p["nombre"]}">{p["nombre"]}</option>' for p in pendientes)}
      </select>
    </div>
    <div class="form-group">
      <label>Nombre del participante</label>
      <input type="text" id="txNombre" placeholder="Ej: Juana Pérez" style="max-width:400px;" list="teams-list" autocomplete="off">
    </div>

    {datalists_html}

    <div class="section-title">🏟️ Fase de Grupos</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;" id="txGrupos"></div>

    <div class="section-title">⚽ Bracket — 16avos (lado izquierdo)</div>
    <div class="bracket-side">{slots_html(slots_izq, 'si', 0)}</div>

    <div class="section-title">⚽ Bracket — 16avos (lado derecho)</div>
    <div class="bracket-side">{slots_html(slots_der, 'sd', 0)}</div>

    <div class="section-title">🏆 Finales</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;max-width:500px;">
      <div><label>🏆 Campeón</label><input type="text" id="txCamp" list="teams-all" autocomplete="off"></div>
      <div><label>🥈 Segundo</label><input type="text" id="txSeg" list="teams-all" autocomplete="off"></div>
      <div><label>🥉 Tercero</label><input type="text" id="txTerc" list="teams-all" autocomplete="off"></div>
      <div><label>4to puesto</label><input type="text" id="txCuarto" list="teams-all" autocomplete="off"></div>
    </div>
    
    <div style="margin-top:20px;display:flex;gap:10px;flex-wrap:wrap;">
      <button class="btn" onclick="generarJSON()">📄 Generar JSON</button>
      <button class="btn btn-green" onclick="copiarJSON()">📋 Copiar al portapapeles</button>
      <button class="btn btn-outline btn-sm" onclick="limpiarForm()">🗑️ Limpiar</button>
    </div>
    <textarea id="txOutput" style="margin-top:14px;height:200px;font-family:'SF Mono',monospace;font-size:0.72rem;" placeholder="El JSON aparecerá aquí..."></textarea>
    <div style="font-size:0.7rem;color:var(--muted);margin-top:4px;">
      Copiá el JSON → creá el archivo en <code>data/pollas/</code> → ejecutá <code>python3 scripts/calificar.py</code>
    </div>
  </div>

  <!-- Resultados y API -->
  <div class="card">
    <h3 style="color:var(--navy);margin-bottom:14px;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.06em;">🔧 Gestión de resultados</h3>
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;">
      <button class="btn btn-sm" onclick="generarPrueba()">🧪 Generar datos de prueba</button>
      <button class="btn btn-sm" onclick="fetchAPI()" id="btnAPI">🌐 Consultar API (worldcup26.ir)</button>
      <button class="btn btn-outline btn-sm" onclick="document.getElementById('resOutput').select();document.execCommand('copy');showToast('📋 Copiado')">📋 Copiar</button>
    </div>
    <textarea id="resOutput" style="height:180px;font-family:'SF Mono',monospace;font-size:0.7rem;" placeholder="Acá aparecerán los datos de prueba o de la API..."></textarea>
    <div style="font-size:0.68rem;color:var(--muted);margin-top:6px;">
      Copiá el JSON → reemplazá <code>data/resultados_reales.json</code> → ejecutá <code>python3 scripts/calificar.py && python3 scripts/generar_sitio.py</code>
    </div>
  </div>

  <!-- Pagos -->
  <div class="card">
    <h3 style="color:var(--navy);margin-bottom:16px;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.06em;">💳 Confirmación de pagos</h3>
    <div class="table-wrap"><table>
      <thead><tr><th>Participante</th><th>WhatsApp</th><th>Pollas</th><th>Pagado</th><th>Monto</th></tr></thead>
      <tbody id="pagosTable"></tbody>
    </table></div>
    <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
      <button class="btn btn-sm" onclick="agregarParticipante()">+ Agregar participante</button>
      <button class="btn btn-green btn-sm" onclick="guardarPagos()">💾 Guardar</button>
      <span style="font-size:0.7rem;color:var(--muted);margin-left:auto;">Cambios en localStorage</span>
    </div>
  </div>

  <div id="toast" class="toast">✅ Listo</div>
</div>

<script>
const PASSWORD = "{ADMIN_PASSWORD}";
const COSTO = {costo};
const GRUPOS = ['A','B','C','D','E','F','G','H','I','J','K','L'];
const SLOTS_IZQ = {json.dumps(slots_izq)};
const SLOTS_DER = {json.dumps(slots_der)};
const PENDIENTES = {pendientes_json};

let participantes = {partes_json};

// ── Lock ──
function unlock() {{
  if (document.getElementById('pwdInput').value === PASSWORD) {{
    document.getElementById('lockScreen').classList.add('hidden');
    document.getElementById('adminContent').classList.remove('hidden');
    renderAll();
  }} else {{
    document.getElementById('lockError').style.display = 'block';
  }}
}}
document.getElementById('pwdInput').addEventListener('keydown', e => {{ if (e.key==='Enter') unlock(); }});

// ── Pending files ──
function renderPending() {{
  let h = '';
  PENDIENTES.forEach(f => {{
    const esExcel = f.tipo === 'xlsx';
    const ruta = esExcel ? '../data/excel/' + f.nombre.replace('[Excel] ','') : '../pendientes/' + f.nombre;
    h += `<div class="file-item">
      <a href="${{ruta}}" target="_blank" class="file-name" style="text-decoration:none;color:var(--navy);">📄 ${{f.nombre}}</a>
      <span class="file-badge ${{f.tipo}}">${{f.tipo.toUpperCase()}}</span>
    </div>`;
  }});
  if (!h) h = '<div style="color:var(--muted);font-size:0.8rem;">Ningún archivo pendiente 🎉</div>';
  document.getElementById('pendingList').innerHTML = h;
}}

function fillNombre(sel) {{
  const name = sel.value.replace(/Polla Mundialista /i,'').replace(/Final \\d /i,'').replace(/\\.(pdf|jpg|jpeg)$/i,'').trim();
  document.getElementById('txNombre').value = name || '';
}}

// ── Grupos form ──
function renderGrupos() {{
  let h = '';
  GRUPOS.forEach(g => {{
    h += `<div style="background:#f8fafc;border-radius:10px;padding:14px;border:1px solid var(--card-border);">
      <strong style="font-size:0.75rem;color:var(--navy);">Grupo ${{g}}</strong>
      <div style="margin-top:6px;display:flex;flex-direction:column;gap:5px;">
        ${{[1,2,3,4].map(p => `
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="font-size:0.7rem;color:var(--muted);width:16px;text-align:center;">${{p}}°</span>
            <input type="text" id="g${{g}}_${{p}}" placeholder="Equipo" style="flex:1;font-size:0.78rem;padding:7px 10px;" list="g-${{g}}" autocomplete="off">
          </div>
        `).join('')}}
      </div>
    </div>`;
  }});
  document.getElementById('txGrupos').innerHTML = h;
}}

// ── Pagos ──
function loadPagos() {{
  const saved = localStorage.getItem('pollas_participantes');
  if (saved) participantes = JSON.parse(saved);
}}

function renderPagos() {{
  let h = '';
  let totalAcum = 0;
  participantes.forEach((p, pi) => {{
    const numPollas = p.pollas || 1;
    for (let i = 0; i < numPollas; i++) {{
      const letra = numPollas > 1 ? String.fromCharCode(65 + i) : '';
      const monto = p.pago ? COSTO : 0;
      totalAcum += monto;
      h += `<tr>
        <td style="text-align:left;font-weight:600;">${{p.nombre}}${{letra ? ' <span class="polla-tag">'+letra+'</span>' : ''}}</td>
        <td>${{i===0 ? (p.whatsapp||'-') : ''}}</td>
        <td>Polla ${{letra || 'Única'}}</td>
        <td>${{i===0 ? '<label class="toggle"><input type="checkbox" '+(p.pago?'checked':'')+' onchange="togglePago('+pi+')"><span class="slider"></span></label>' : '<span class="status '+(p.pago?'pagado':'pendiente')+'">'+(p.pago?'✓ Pagado':'✗ Pendiente')+'</span>'}}</td>
        <td style="color:var(--gold);font-weight:700;">$${{monto}}</td>
      </tr>`;
    }}
  }});
  if (!h) h = '<tr><td colspan="5" style="color:var(--muted);">Sin participantes</td></tr>';
  h += `<tr style="border-top:2px solid var(--card-border);font-weight:700;">
    <td colspan="4" style="text-align:right;color:var(--navy);">💰 Acumulado</td>
    <td style="color:var(--gold);font-size:1.1rem;">$${{totalAcum}}</td>
  </tr>`;
  document.getElementById('pagosTable').innerHTML = h;
}}

function togglePago(i) {{ participantes[i].pago = !participantes[i].pago; }}
function agregarParticipante() {{
  const nombre = prompt('Nombre:');
  if (!nombre) return;
  const pollas = parseInt(prompt('Cantidad de pollas:', '1')) || 1;
  const whatsapp = prompt('WhatsApp (opcional):') || '';
  participantes.push({{nombre, whatsapp, pollas, pago: false}});
  renderPagos();
}}

function guardarPagos() {{
  localStorage.setItem('pollas_participantes', JSON.stringify(participantes));
  showToast('✅ Pagos guardados');
}}

// ── Transcripción ──
function generarJSON() {{
  const data = {{
    archivo_original: document.getElementById('txArchivo').value,
    participante: document.getElementById('txNombre').value,
    formato_original: "pdf",
    grupos: {{}},
    ronda_16avos: [],
    ronda_8avos: [],
    ronda_cuartos: [],
    ronda_semifinales: [],
    finales: {{
      campeon: document.getElementById('txCamp').value.trim(),
      segundo: document.getElementById('txSeg').value.trim(),
      tercero: document.getElementById('txTerc').value.trim(),
      cuarto: document.getElementById('txCuarto').value.trim(),
    }}
  }};
  
  GRUPOS.forEach(g => {{
    const eqs = {{}};
    [1,2,3,4].forEach(p => {{
      const v = document.getElementById('g'+g+'_'+p).value.trim();
      if (v) eqs[v] = p;
    }});
    if (Object.keys(eqs).length) data.grupos[g] = eqs;
  }});
  
  SLOTS_IZQ.forEach((slot, i) => {{
    const eq = document.getElementById('si'+i).value.trim();
    if (eq) data.ronda_16avos.push({{slot, equipo: eq}});
  }});
  SLOTS_DER.forEach((slot, i) => {{
    const eq = document.getElementById('sd'+i).value.trim();
    if (eq) data.ronda_16avos.push({{slot, equipo: eq}});
  }});
  
  document.getElementById('txOutput').value = JSON.stringify(data, null, 2);
}}

function copiarJSON() {{
  generarJSON();
  const ta = document.getElementById('txOutput');
  ta.select(); ta.setSelectionRange(0, 99999);
  document.execCommand('copy');
  showToast('📋 JSON copiado al portapapeles');
}}

function limpiarForm() {{
  document.querySelectorAll('#adminContent input[type=text], #adminContent textarea').forEach(el => el.value = '');
  document.getElementById('txOutput').value = '';
  showToast('🗑️ Formulario limpiado');
}}

function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}}

// ── Resultados: prueba y API ──
const EQUIPOS = {equipos_json};

function generarPrueba() {{
  // Datos de prueba basados en ranking FIFA
  const gruposPrueba = {{
    A: {{"🇲🇽 México":1,"🇰🇷 Corea del Sur":2,"🇿🇦 Sudáfrica":3,"🇨🇿 Rep. Checa":4}},
    B: {{"🇨🇭 Suiza":1,"🇨🇦 Canadá":2,"🇧🇦 Bosnia y Herzegovina":3,"🇶🇦 Qatar":4}},
    C: {{"🇧🇷 Brasil":1,"🇲🇦 Marruecos":2,"🏴󠁧󠁢󠁳󠁣󠁴󠁿 Escocia":3,"🇭🇹 Haití":4}},
    D: {{"🇺🇸 Estados Unidos":1,"🇵🇾 Paraguay":2,"🇦🇺 Australia":3,"🇹🇷 Turquía":4}},
    E: {{"🇩🇪 Alemania":1,"🇪🇨 Ecuador":2,"🇨🇮 Costa de Marfil":3,"🇨🇼 Curazao":4}},
    F: {{"🇳🇱 Holanda":1,"🇯🇵 Japón":2,"🇸🇪 Suecia":3,"🇹🇳 Túnez":4}},
    G: {{"🇧🇪 Bélgica":1,"🇮🇷 Irán":2,"🇪🇬 Egipto":3,"🇳🇿 Nueva Zelanda":4}},
    H: {{"🇪🇸 España":1,"🇺🇾 Uruguay":2,"🇸🇦 Arabia Saudí":3,"🇨🇻 Cabo Verde":4}},
    I: {{"🇫🇷 Francia":1,"🇸🇳 Senegal":2,"🇳🇴 Noruega":3,"🇮🇶 Irak":4}},
    J: {{"🇦🇷 Argentina":1,"🇦🇹 Austria":2,"🇩🇿 Argelia":3,"🇯🇴 Jordania":4}},
    K: {{"🇵🇹 Portugal":1,"🇨🇴 Colombia":2,"🇨🇩 Rep. Congo":3,"🇺🇿 Uzbekistán":4}},
    L: {{"🇬🇧 Inglaterra":1,"🇭🇷 Croacia":2,"🇬🇭 Ghana":3,"🇵🇦 Panamá":4}},
  }};
  
  const slots = [
    {{s:"1E",e:"🇩🇪 Alemania"}},{{s:"3 ABCDF",e:"🇪🇬 Egipto"}},{{s:"1I",e:"🇫🇷 Francia"}},{{s:"3 CDFGH",e:"🏴󠁧󠁢󠁳󠁣󠁴󠁿 Escocia"}},
    {{s:"2A",e:"🇰🇷 Corea del Sur"}},{{s:"2B",e:"🇨🇦 Canadá"}},{{s:"1F",e:"🇳🇱 Holanda"}},{{s:"2C",e:"🇲🇦 Marruecos"}},
    {{s:"2K",e:"🇨🇴 Colombia"}},{{s:"2L",e:"🇭🇷 Croacia"}},{{s:"1H",e:"🇪🇸 España"}},{{s:"2J",e:"🇦🇹 Austria"}},
    {{s:"1D",e:"🇺🇸 Estados Unidos"}},{{s:"3 BEFIJ",e:"🇸🇪 Suecia"}},{{s:"1G",e:"🇧🇪 Bélgica"}},{{s:"3 AEFHIJ",e:"🇳🇴 Noruega"}},
    {{s:"1C",e:"🇧🇷 Brasil"}},{{s:"2F",e:"🇯🇵 Japón"}},{{s:"2E",e:"🇪🇨 Ecuador"}},{{s:"2I",e:"🇸🇳 Senegal"}},
    {{s:"1A",e:"🇲🇽 México"}},{{s:"3 CEFHI",e:"🇨🇮 Costa de Marfil"}},{{s:"1L",e:"🇬🇧 Inglaterra"}},{{s:"3 EHIJK",e:"🇿🇦 Sudáfrica"}},
    {{s:"1J",e:"🇦🇷 Argentina"}},{{s:"2H",e:"🇺🇾 Uruguay"}},{{s:"2D",e:"🇵🇾 Paraguay"}},{{s:"2G",e:"🇮🇷 Irán"}},
    {{s:"1B",e:"🇨🇭 Suiza"}},{{s:"3 EFGIJ",e:"🇦🇺 Australia"}},{{s:"1K",e:"🇵🇹 Portugal"}},{{s:"3 DEIJL",e:"🇬🇭 Ghana"}},
  ];
  
  const data = {{
    _nota: "Datos de prueba FIFA — reemplazar con resultados reales",
    grupos: gruposPrueba,
    ronda_16avos: slots,
    ronda_8avos: [
      {{e:"🇩🇪 Alemania"}},{{e:"🇫🇷 Francia"}},{{e:"🇳🇱 Holanda"}},{{e:"🇲🇦 Marruecos"}},
      {{e:"🇪🇸 España"}},{{e:"🇨🇴 Colombia"}},{{e:"🇺🇸 Estados Unidos"}},{{e:"🇧🇪 Bélgica"}},
      {{e:"🇧🇷 Brasil"}},{{e:"🇸🇳 Senegal"}},{{e:"🇲🇽 México"}},{{e:"🇬🇧 Inglaterra"}},
      {{e:"🇦🇷 Argentina"}},{{e:"🇺🇾 Uruguay"}},{{e:"🇨🇭 Suiza"}},{{e:"🇵🇹 Portugal"}},
    ].map(x=>({{equipo:x.e}})),
    ronda_cuartos: [
      {{e:"🇫🇷 Francia"}},{{e:"🇪🇸 España"}},{{e:"🇧🇪 Bélgica"}},{{e:"🇳🇱 Holanda"}},
      {{e:"🇧🇷 Brasil"}},{{e:"🇬🇧 Inglaterra"}},{{e:"🇦🇷 Argentina"}},{{e:"🇵🇹 Portugal"}},
    ].map(x=>({{equipo:x.e}})),
    ronda_semifinales: [
      {{e:"🇫🇷 Francia"}},{{e:"🇪🇸 España"}},{{e:"🇧🇷 Brasil"}},{{e:"🇦🇷 Argentina"}},
    ].map(x=>({{equipo:x.e}})),
    finales: {{campeon:"🇦🇷 Argentina",segundo:"🇫🇷 Francia",tercero:"🇧🇷 Brasil",cuarto:"🇪🇸 España"}},
  }};
  
  document.getElementById('resOutput').value = JSON.stringify(data, null, 2);
  showToast('🧪 Datos de prueba generados');
}}

async function fetchAPI() {{
  const btn = document.getElementById('btnAPI');
  btn.textContent = '⏳ Consultando...';
  btn.disabled = true;
  
  try {{
    const resp = await fetch('https://worldcup26.ir/get/teams');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const teamsData = await resp.json();
    
    const out = {{
      _nota: 'Datos desde worldcup26.ir',
      equipos: teamsData.teams?.length || 0,
      raw: teamsData,
    }};
    
    document.getElementById('resOutput').value = JSON.stringify(out, null, 2);
    showToast('✅ API: ' + (out.equipos||0) + ' equipos');
  }} catch(e) {{
    const msg = e.message.includes('Failed to fetch') || e.message.includes('NetworkError')
      ? '❌ Error CORS: la API no permite consultas desde local.\n\nUsá el script Python en su lugar:\n  python3 scripts/fetch_resultados.py --api\n\n(O publicá el sitio en GitHub Pages — ahí funciona sin CORS)'
      : 'Error: ' + e.message;
    document.getElementById('resOutput').value = msg;
    showToast('❌ ' + (e.message.includes('Failed') ? 'CORS bloqueado' : 'Error API'));
  }}
  
  btn.textContent = '🌐 Consultar API (worldcup26.ir)';
  btn.disabled = false;
}}

function renderAll() {{
  renderPending();
  renderGrupos();
  renderPagos();
}}

loadPagos();
</script>
</body>
</html>"""

def main():
    if not PUNTAJES_FILE.exists():
        print("❌ No existe puntajes.json. Ejecutá calificar.py primero.")
        return
    
    with open(PUNTAJES_FILE, encoding="utf-8") as f:
        puntajes = json.load(f)
    
    if PARTICIPANTES_FILE.exists():
        with open(PARTICIPANTES_FILE, encoding="utf-8") as f:
            participantes = json.load(f)
    else:
        participantes = {"costo_por_polla": 10, "participantes": []}
    
    SALIDA_PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    
    with open(SALIDA_PUBLIC, "w", encoding="utf-8") as f:
        f.write(generar_publica(puntajes, participantes))
    print(f"✅ Pública: {SALIDA_PUBLIC} ({len(open(SALIDA_PUBLIC).read())/1024:.1f} KB)")
    
    with open(SALIDA_ADMIN, "w", encoding="utf-8") as f:
        f.write(generar_admin(participantes))
    print(f"✅ Admin:   {SALIDA_ADMIN} ({len(open(SALIDA_ADMIN).read())/1024:.1f} KB)")
    print(f"\n🔑 Admin: {ADMIN_PASSWORD}")

if __name__ == "__main__":
    main()
