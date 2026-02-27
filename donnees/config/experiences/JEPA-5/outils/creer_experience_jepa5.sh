#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash outils/creer_experience_jepa5.sh
#   (peut être lancé de n'importe où dans le repo)

if ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  :
else
  echo "[ERREUR] pas dans un repo git (ou git indisponible). Lance depuis la racine du repo."
  exit 1
fi

SRC="$ROOT/donnees/config/experiences/JEPA-4"
DST="$ROOT/donnees/config/experiences/JEPA-5"

if [[ ! -d "$SRC" ]]; then
  echo "[ERREUR] Source absente: $SRC"
  exit 1
fi

if [[ -d "$DST" ]]; then
  echo "[INFO] JEPA-5 existe déjà: $DST"
  exit 0
fi

echo "[JEPA-5] copie: $SRC -> $DST"
mkdir -p "$DST"
cp -a "$SRC/." "$DST/"

# Ajuste experience.yml si présent (remplace le nom d'expérience)
if [[ -f "$DST/experience.yml" ]]; then
  sed -i 's/JEPA-4/JEPA-5/g' "$DST/experience.yml"
fi

# Ajuste README
cat > "$DST/README.md" <<'MD'
# JEPA-5 — adaptation locale des hypothèses (v1)

## intention
au lieu de garder un ensemble fixe ou une compétition winner-take-all, on adapte les poids des hypothèses au fil des transitions selon leur performance.

## signaux par transition
- s1 = mse(yhat1, y)
- s2 = mse(yhat2, y)
- ema_s1, ema_s2 (moyenne mobile exponentielle)
- w1, w2 (poids adaptatifs, w1+w2=1)
- yhat = w1*yhat1 + w2*yhat2
- surprise = mse(yhat, y)
- disagree = mse(yhat1, yhat2) (optionnel mais recommandé)

## gate (proposition)
inconnu si surprise > seuil_surprise OU disagree > seuil_disagree
(seuils par quantiles)

## critères de succès
- les poids w1/w2 ne sont pas dégénérés (pas ~1.0 constant)
- les poids se déplacent selon des régimes (variabilité mesurable)
- gate produit une partition intéressante
- action conforme contrat
MD

# Crée/écrase un fichier de config JEPA-5 pour l'épreuve si tu veux isoler le mode
# (tu adapteras à ton format exact de config_epreuve.json)
EPREUVE_CFG="$DST/plan/config_epreuve.json"
if [[ -f "$EPREUVE_CFG" ]]; then
  python - <<'PY'
import json, pathlib
p = pathlib.Path("donnees/config/experiences/JEPA-5/plan/config_epreuve.json")
cfg = json.loads(p.read_text(encoding="utf-8"))
cfg["mode"] = "adaptive"  # nouveau mode JEPA-5
cfg.setdefault("adaptive", {})
cfg["adaptive"].update({
  "alpha_ema": 0.97,
  "temperature": 0.25,
  "poids_min": 0.05,
})
p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("[JEPA-5] config_epreuve.json mis à jour: mode=adaptive")
PY
else
  echo "[WARN] $EPREUVE_CFG absent (ok si ton pipeline n'utilise pas ce fichier)."
fi

echo "[JEPA-5] créé: $DST"
echo "[JEPA-5] prochain test:"
echo "  export PYTHONPATH=services"
echo "  python -m ui_cli.app.pipeline.cli_pipeline run --experience JEPA-5 --phase all --seed 123"
