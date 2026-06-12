#!/bin/bash
# actualizar.sh — Pipeline completo post-partido
# Uso: bash actualizar.sh

cd "$(dirname "$0")/.."

echo "📡 1/4 Obteniendo resultados de la API..."
python3 scripts/fetch_resultados.py --api

echo ""
echo "📊 2/4 Calculando puntajes..."
python3 scripts/calificar.py

echo ""
echo "🌐 3/4 Generando sitio web..."
python3 scripts/generar_sitio.py

echo ""
echo "🚀 4/4 Subiendo a GitHub..."
git add docs/ data/resultados_reales.json data/puntajes.json
git commit -m "Actualización automática post-partido" || echo "(sin cambios)"
git push

echo ""
echo "✅ Listo: https://joseurgilesc.github.io/webPollaMundialista/"
