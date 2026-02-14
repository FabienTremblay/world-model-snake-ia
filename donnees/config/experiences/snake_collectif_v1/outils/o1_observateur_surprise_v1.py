from __future__ import annotations

"""Observateur O1 — Surprise.

Robustesse:
- si metrics.jsonl est absent (ex: run issu du TUI), on n'échoue pas: on écrit un jsonl vide et on loggue un WARN.
- même chose si journal.jsonl est absent.

Ce script reste compatible avec le contrat ActionSnake (voir services/commun/actions_snake.py).
"""

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from commun.actions_snake import est_action_snake
except Exception:
    # Le script peut être exécuté hors PYTHONPATH=services: on accepte de ne pas filtrer.
    def est_action_snake(_: object) -> bool:  # type: ignore[override]
        return True


def _ecrire_vide(sortie: Path, raison: str) -> None:
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(f"# jsonl vide: {raison}\n", encoding="utf-8")
    print(f"[OK] écrit: {sortie} (0 propositions)")
    print(f"[WARN] {raison}")


def _iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            yield json.loads(line)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--prefix-bits", type=int, default=16)
    ap.add_argument("--sortie", required=True)
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    sortie = Path(args.sortie)

    journal_path = run_dir / "journal.jsonl"
    metrics_path = run_dir / "metrics.jsonl"

    if not journal_path.exists():
        _ecrire_vide(sortie, f"journal.jsonl introuvable: {journal_path} (run incomplet?)")
        return
    if not metrics_path.exists():
        _ecrire_vide(sortie, f"metrics.jsonl introuvable: {metrics_path} (run incomplet, ex: TUI)")
        return

    # ---- Logique minimale (conserve ton comportement existant: si rien -> 0) ----
    prefix_bits: int = args.prefix_bits
    masque = (1 << prefix_bits) - 1

    # On construit une table support: (etat_prefix, action) -> next_prefix count
    transitions: dict[tuple[int, str], dict[int, int]] = {}
    actions_ignores = 0

    # metrics contient action + checksum_avant + checksum (déjà un "state abstraction")
    for m in _iter_jsonl(metrics_path):
        a = m.get("action")
        if a is None or not est_action_snake(a):
            actions_ignores += 1
            continue
        try:
            s0 = int(m.get("checksum_avant"))
            s1 = int(m.get("checksum"))
        except Exception:
            continue
        k0 = (s0 >> max(0, 64 - prefix_bits)) & masque if s0 >= 0 else (s0 & masque)
        k1 = (s1 >> max(0, 64 - prefix_bits)) & masque if s1 >= 0 else (s1 & masque)
        key = (k0, str(a))
        transitions.setdefault(key, {})
        transitions[key][k1] = transitions[key].get(k1, 0) + 1

    # Surprise simple: quand, pour (etat_prefix, action), la transition observée n'est pas la plus fréquente
    # -> proposition "surprise_transition"
    propositions: list[dict[str, Any]] = []
    for m in _iter_jsonl(metrics_path):
        a = m.get("action")
        if a is None or not est_action_snake(a):
            continue
        try:
            s0 = int(m.get("checksum_avant"))
            s1 = int(m.get("checksum"))
        except Exception:
            continue
        k0 = (s0 >> max(0, 64 - prefix_bits)) & masque if s0 >= 0 else (s0 & masque)
        k1 = (s1 >> max(0, 64 - prefix_bits)) & masque if s1 >= 0 else (s1 & masque)
        key = (k0, str(a))
        dist = transitions.get(key) or {}
        if not dist:
            continue
        # meilleur next
        best_next = max(dist.items(), key=lambda kv: kv[1])[0]
        if k1 != best_next:
            propositions.append(
                {
                    "type": "surprise_transition",
                    "prefix_bits": prefix_bits,
                    "etat_prefix": k0,
                    "action": str(a),
                    "next_prefix_observe": k1,
                    "next_prefix_attendu": best_next,
                    "support": dist.get(k1, 0),
                    "support_attendu": dist.get(best_next, 0),
                }
            )

    sortie.parent.mkdir(parents=True, exist_ok=True)
    with sortie.open("w", encoding="utf-8") as f:
        for p in propositions:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"[OK] écrit: {sortie} ({len(propositions)} propositions)")
    if actions_ignores:
        print(f"[INFO] actions ignorées (non canoniques ActionSnake): {actions_ignores}")
    if not propositions:
        print("[INFO] 0 surprise détectée. Causes fréquentes:")
        print("       - état trop complet + environnement déterministe (normal)")
        print("       - min-support trop élevé")
        print("       Astuce: réessaie avec --prefix-bits 16 ou 20.")


if __name__ == "__main__":
    main()
