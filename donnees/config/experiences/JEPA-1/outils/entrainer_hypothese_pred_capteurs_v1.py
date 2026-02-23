from __future__ import annotations

import argparse, json, os, random, time
from typing import Any, Dict, Tuple, List

import torch
import torch.nn as nn
import torch.nn.functional as F

ACTIONS = ["avant", "observer_gauche", "observer_droite"]


class ModelePredCapteurs(nn.Module):
    def __init__(self, dim_in: int, hidden: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim_in, hidden),
            nn.ReLU(),
            nn.Linear(hidden, dim_in),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def charger_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def charger_dataset_paires(pt_path: str, device: str) -> Tuple[torch.Tensor, torch.Tensor]:
    obj = torch.load(pt_path, map_location="cpu")
    x = obj["x"].float()
    y = obj["y"].float()
    return x.to(device), y.to(device)


def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def sauvegarder_agent_personne_spec(sortie_dir: str, plan: Dict[str, Any], cfg: Dict[str, Any]) -> str:
    ensure_dir(os.path.join(sortie_dir, "agents"))
    spec = {
        "agent_personne_id": plan.get("agent_personne_id", "agent_personne_inconnu"),
        "experience": cfg.get("experience"),
        "contrat_actions": plan.get("contrat_actions", ACTIONS),
        "hypotheses": plan.get("hypotheses", []),
        "tronc": plan.get("tronc", {}),
        "tetes": plan.get("tetes", []),
        "artefacts": {"poids_pt": "artefacts/poids/agent_personne.poids.pt"},
        "horodatage": time.strftime("%Y-%m-%d_%Hh%M"),
    }
    out_path = os.path.join(sortie_dir, "agents", "agent_personne.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    return out_path


def _quantiles_numpy(values: List[float], qs: List[float]) -> Dict[str, float]:
    import numpy as np
    arr = np.array(values, dtype=np.float64)
    out = {}
    for q in qs:
        out[f"p{int(q*100):02d}"] = float(np.quantile(arr, q))
    return out


def entrainer(cfg_path: str) -> None:
    cfg = charger_config(cfg_path)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(cfg_path), ".."))

    plan_path = os.path.join(base_dir, cfg["agent_personne_plan"])
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    seed = int(cfg["entrainement"]["seed"])
    set_seed(seed)

    device = cfg["entrainement"].get("device", "cpu")
    x, y = charger_dataset_paires(os.path.join(base_dir, cfg["dataset_paires_pt"]), device=device)

    dim = int(cfg["capteurs"]["dim_vecteur"])

    hyp_ref = plan["hypotheses"][0]["ref"]
    hyp_file = os.path.join(base_dir, hyp_ref)
    with open(hyp_file, "r", encoding="utf-8") as f:
        hyp = json.load(f)
    hidden = int(hyp.get("hyperparams", {}).get("hidden", 64))

    assert x.shape[1] == dim and y.shape[1] == dim, f"dim mismatch: x={x.shape}, y={y.shape}, dim={dim}"

    model = ModelePredCapteurs(dim_in=dim, hidden=hidden).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=float(cfg["entrainement"]["lr"]))

    bs = int(cfg["entrainement"]["batch_size"])
    epochs = int(cfg["entrainement"]["epochs"])

    n = x.shape[0]
    indices = torch.arange(n, device=device)

    model.train()
    hist = []
    for ep in range(1, epochs + 1):
        perm = indices[torch.randperm(n)]
        total = 0.0
        nb = 0
        for i in range(0, n, bs):
            batch = perm[i:i+bs]
            xb = x[batch]
            yb = y[batch]
            pred = model(xb)
            loss = F.mse_loss(pred, yb)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            total += float(loss.item()) * xb.shape[0]
            nb += xb.shape[0]
        mse = total/nb
        hist.append(mse)
        print(f"[epoch {ep}/{epochs}] mse={mse:.6f}")

    sortie_dir = os.path.join(base_dir, cfg["sortie_dir"])
    ensure_dir(os.path.join(sortie_dir, "poids"))
    poids_path = os.path.join(sortie_dir, "poids", "agent_personne.poids.pt")
    torch.save({"modele_pred_capteurs": model.state_dict(), "dim": dim, "hidden": hidden, "seed": seed}, poids_path)

    spec_path = sauvegarder_agent_personne_spec(sortie_dir, plan, cfg)

    ensure_dir(os.path.join(sortie_dir, "resultats"))
    rapport_path = os.path.join(sortie_dir, "resultats", "rapport_entrainement.json")
    rapport = {
        "epochs": epochs, "batch_size": bs, "lr": cfg["entrainement"]["lr"], "seed": seed,
        "poids": os.path.relpath(poids_path, base_dir),
        "spec": os.path.relpath(spec_path, base_dir),
        "mse_par_epoch": hist,
    }
    with open(rapport_path, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)

    print("OK:", os.path.relpath(spec_path, base_dir))
    print("OK:", os.path.relpath(poids_path, base_dir))
    print("OK:", os.path.relpath(rapport_path, base_dir))


def _calculer_seuil_depuis_surprise(surprises: torch.Tensor, gate_cfg: Dict[str, Any]) -> float:
    mode = gate_cfg.get("mode", "seuil")
    seuil = float(gate_cfg.get("seuil_connu", 0.10))
    if mode == "quantile":
        q = float(gate_cfg.get("quantile", 0.90))
        q = min(max(q, 0.0), 1.0)
        try:
            seuil = float(torch.quantile(surprises, q).item())
        except Exception:
            s = surprises.detach().cpu().numpy()
            import numpy as np
            seuil = float(np.quantile(s, q))
    return seuil


def eprouver(cfg_path: str) -> None:
    cfg = charger_config(cfg_path)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(cfg_path), ".."))

    seed = int(cfg["epreuve"]["seed"])
    set_seed(seed)
    device = cfg["epreuve"].get("device", "cpu")

    spec_path = os.path.join(base_dir, cfg["agent_personne_spec"])
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    poids_path = os.path.join(base_dir, cfg["poids_pt"])
    w = torch.load(poids_path, map_location="cpu")
    dim = int(w["dim"])
    hidden = int(w["hidden"])

    model = ModelePredCapteurs(dim_in=dim, hidden=hidden).to(device)
    model.load_state_dict(w["modele_pred_capteurs"])
    model.eval()

    x, y = charger_dataset_paires(os.path.join(base_dir, cfg["dataset_paires_pt"]), device=device)

    bs = int(cfg["epreuve"]["batch_size"])

    out_journal = os.path.join(base_dir, cfg["sorties"]["journal_agent"])
    out_registre = os.path.join(base_dir, cfg["sorties"]["registre_epistemique"])
    out_resultats = os.path.join(base_dir, cfg["sorties"]["resultats"])
    os.makedirs(os.path.dirname(out_journal), exist_ok=True)
    os.makedirs(os.path.dirname(out_registre), exist_ok=True)
    os.makedirs(os.path.dirname(out_resultats), exist_ok=True)

    # Passe 1: surprises
    all_surprises = []
    with torch.no_grad():
        for i in range(0, x.shape[0], bs):
            xb = x[i:i+bs]
            yb = y[i:i+bs]
            pred = model(xb)
            mse_item = ((pred - yb) ** 2).mean(dim=1)  # [B]
            all_surprises.append(mse_item.detach().cpu())
    all_surprises = torch.cat(all_surprises, dim=0)  # [N]

    gate_cfg = cfg.get("gate", {})
    seuil_connu = _calculer_seuil_depuis_surprise(all_surprises, gate_cfg)

    # Policy
    alt = 0
    total = 0
    nb_connu = 0
    nb_inconnu = 0
    total_mse = 0.0

    strategie_inconnu = cfg.get("policy", {}).get("strategie_inconnu", "observer_gauche_ou_droite")
    strategie_connu = cfg.get("policy", {}).get("strategie_connu", "avant")

    def choisir_action(strat: str) -> str:
        nonlocal alt
        if strat == "avant":
            return "avant"
        if strat == "observer_gauche":
            return "observer_gauche"
        if strat == "observer_droite":
            return "observer_droite"
        a = "observer_gauche" if (alt % 2 == 0) else "observer_droite"
        alt += 1
        return a

    s_list = [float(v.item()) for v in all_surprises]
    import numpy as np
    arr = np.array(s_list, dtype=np.float64)
    stats = {
        "n": int(arr.size),
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "quantiles": _quantiles_numpy(s_list, [0.50, 0.75, 0.90, 0.95, 0.99]),
    }

    registre = {
        "experience": cfg.get("experience"),
        "agent_personne_id": spec.get("agent_personne_id"),
        "gate": {
            "mode": gate_cfg.get("mode", "seuil"),
            "quantile": gate_cfg.get("quantile"),
            "seuil_connu": seuil_connu,
            "stats_surprise": stats,
        },
        "hypotheses": {
            "h_pred_capteurs_proj_t1_v1": {
                "nb_tests": 0,
                "mse_moyenne": 0.0,
                "mse_quantiles": stats["quantiles"],
            }
        }
    }

    with open(out_journal, "w", encoding="utf-8") as jf:
        for idx in range(all_surprises.shape[0]):
            surprise = float(all_surprises[idx].item())
            connu = surprise <= seuil_connu

            if connu:
                mode = "connu_exploiter"
                action = choisir_action(strategie_connu)
                nb_connu += 1
            else:
                mode = "inconnu_explorer"
                action = choisir_action(strategie_inconnu)
                nb_inconnu += 1

            assert action in ACTIONS, f"action invalide: {action}"

            jf.write(json.dumps({
                "idx": total,
                "mode": mode,
                "surprise": surprise,
                "seuil_connu": seuil_connu,
                "action": action,
                "agent_id": spec.get("agent_personne_id"),
                "experience": cfg.get("experience"),
            }, ensure_ascii=False) + "\n")

            total_mse += surprise
            total += 1

    registre["hypotheses"]["h_pred_capteurs_proj_t1_v1"]["nb_tests"] = total
    registre["hypotheses"]["h_pred_capteurs_proj_t1_v1"]["mse_moyenne"] = (total_mse / max(total, 1))
    registre["gate"]["effet"] = {
        "nb_connu": nb_connu,
        "nb_inconnu": nb_inconnu,
        "ratio_inconnu": nb_inconnu / max(total, 1),
        "ratio_connu": nb_connu / max(total, 1),
    }

    with open(out_registre, "w", encoding="utf-8") as f:
        json.dump(registre, f, ensure_ascii=False, indent=2)

    resultats = {
        "experience": cfg.get("experience"),
        "agent_personne_id": spec.get("agent_personne_id"),
        "nb_tests": total,
        "surprise_moyenne": total_mse / max(total, 1),
        "nb_connu": nb_connu,
        "nb_inconnu": nb_inconnu,
        "ratio_connu": nb_connu / max(total, 1),
        "ratio_inconnu": nb_inconnu / max(total, 1),
        "seuil_connu": seuil_connu,
        "gate_mode": gate_cfg.get("mode", "seuil"),
        "gate_quantile": gate_cfg.get("quantile"),
        "journaux": {
            "journal_agent": cfg["sorties"]["journal_agent"],
            "registre_epistemique": cfg["sorties"]["registre_epistemique"]
        }
    }
    with open(out_resultats, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)

    print("OK:", cfg["sorties"]["journal_agent"])
    print("OK:", cfg["sorties"]["registre_epistemique"])
    print("OK:", cfg["sorties"]["resultats"])
    print(f"[gate] seuil_connu={seuil_connu:.8f} (mode={gate_cfg.get('mode','seuil')}, quantile={gate_cfg.get('quantile')})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--mode", choices=["entrainement", "epreuve"], default="entrainement")
    args = ap.parse_args()

    if args.mode == "entrainement":
        entrainer(args.config)
    else:
        eprouver(args.config)


if __name__ == "__main__":
    main()
