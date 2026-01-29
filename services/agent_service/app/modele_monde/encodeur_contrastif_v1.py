# services/agent_service/app/modele_monde/encodeur_contrastif_v1.py
from __future__ import annotations

"""
Encodeur contrastif v1 (sans deep learning lourd).

But du cours 3:
- apprendre une représentation z = E(x) à partir d'observations x (capteurs)
- sans supervision, via apprentissage contrastif InfoNCE
- produire des embeddings normalisés (cosine) utilisables pour un k-means (Q2)

Choix pédagogiques:
- features explicites (histogramme discret de pixels) -> interprétables
- encodeur linéaire W (SGD) -> compréhensible
- augmentation stochastique simple (dropout de bins + bruit faible)

Dépendance unique: numpy
"""

from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

import json
import math
import numpy as np

from commun.contrats import Pixel
from runner.app.replay import decoder_capteurs_b64


def _l2_normaliser(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < eps:
        return v * 0.0
    return v / n


def _softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - np.max(x, axis=axis, keepdims=True)
    ex = np.exp(x)
    s = np.sum(ex, axis=axis, keepdims=True)
    return ex / np.clip(s, 1e-12, None)


def _classe_pixel(px: Pixel) -> int:
    """
    Discrétisation robuste:
    - teinte: 0..359 -> 6 bins
    - intensité: 0..255 -> 4 bins
    => 24 bins
    """
    teinte_bin = int(px.teinte) // 60
    if teinte_bin < 0:
        teinte_bin = 0
    elif teinte_bin > 5:
        teinte_bin = 5

    intens_bin = int(px.intensite) // 64
    if intens_bin < 0:
        intens_bin = 0
    elif intens_bin > 3:
        intens_bin = 3

    return teinte_bin * 4 + intens_bin  # 0..23



def extraire_features_histogramme(capteurs: List[List[Pixel]]) -> np.ndarray:
    """
    Retourne un vecteur (96,) :
      histogrammes (24 bins) sur 4 quadrants (2x2), concaténés.

    Intuition pédagogique : on garde la lisibilité (bins), mais on ajoute une
    structure spatiale minimale pour éviter l'effondrement du latent.
    """
    hauteur = len(capteurs)
    largeur = len(capteurs[0]) if hauteur > 0 else 0
    if hauteur == 0 or largeur == 0:
        return np.zeros((96,), dtype=np.float32)

    mi_y = hauteur // 2
    mi_x = largeur // 2

    H = np.zeros((4, 24), dtype=np.float32)  # 4 quadrants
    T = np.zeros((4,), dtype=np.float32)

    for y, ligne in enumerate(capteurs):
        for x, px in enumerate(ligne):
            q = 0
            if y >= mi_y:
                q += 2
            if x >= mi_x:
                q += 1
            H[q, _classe_pixel(px)] += 1.0
            T[q] += 1.0

    # normaliser chaque quadrant
    for q in range(4):
        if T[q] > 0:
            H[q, :] /= float(T[q])

    return H.reshape(-1).astype(np.float32)


def features_depuis_evt(evt: dict) -> np.ndarray:
    b64 = evt["capteurs_compact"]
    w = int(evt["largeur"])
    h = int(evt["hauteur"])
    capteurs = decoder_capteurs_b64(b64, w, h)
    return extraire_features_histogramme(capteurs)


def augmentation_v1(x: np.ndarray, rng: np.random.Generator, p_drop: float = 0.15, bruit: float = 0.01) -> np.ndarray:
    """
    Augmentation stochastique simple:
    - dropout de bins (masquage) puis renormalisation
    - petit bruit additif (gaussien) puis clamp + renormalisation
    """
    x2 = x.copy()
    if p_drop > 0.0:
        mask = rng.random(size=x2.shape) >= p_drop
        x2 *= mask.astype(np.float32)
    if bruit > 0.0:
        x2 = x2 + rng.normal(0.0, bruit, size=x2.shape).astype(np.float32)
        x2 = np.clip(x2, 0.0, None)
    s = float(np.sum(x2))
    if s > 1e-12:
        x2 /= s
    return x2.astype(np.float32)


@dataclass
class EncodeurContrastifV1:
    """
    Encodeur linéaire: z = normalize(W @ x)
    - W: (d, n_features)
    """
    d: int
    n_features: int = 96
    W: Optional[np.ndarray] = None

    def __post_init__(self) -> None:
        if self.W is None:
            # init petit (stabilité)
            self.W = (0.01 * np.random.randn(self.d, self.n_features)).astype(np.float32)

    def encoder(self, x: np.ndarray) -> np.ndarray:
        z = self.W @ x.astype(np.float32)
        return _l2_normaliser(z.astype(np.float32))

    def encoder_batch(self, X: np.ndarray) -> np.ndarray:
        Z = (X.astype(np.float32) @ self.W.T).astype(np.float32)  # (B,d)
        # normalisation L2 par ligne
        norms = np.linalg.norm(Z, axis=1, keepdims=True)
        Z = Z / np.clip(norms, 1e-12, None)
        return Z.astype(np.float32)

    def sauver_npz(self, path: str) -> None:
        assert self.W is not None
        np.savez(path, d=int(self.d), n_features=int(self.n_features), W=self.W.astype(np.float32))

    @staticmethod
    def charger_npz(path: str) -> "EncodeurContrastifV1":
        data = np.load(path)
        d = int(data["d"])
        n_features = int(data["n_features"])
        W = data["W"].astype(np.float32)
        return EncodeurContrastifV1(d=d, n_features=n_features, W=W)


def _loss_infonce(Z1: np.ndarray, Z2: np.ndarray, tau: float) -> Tuple[float, np.ndarray]:
    """
    InfoNCE symétrique:
      logits = (Z1 @ Z2.T) / tau
      targets = diag (positifs)
    Retourne (loss, P) où P = softmax(logits) (utile pour gradient).
    """
    logits = (Z1 @ Z2.T) / float(tau)  # (B,B)
    P = _softmax(logits, axis=1)       # (B,B)
    # perte: -mean log P[i,i]
    diag = np.clip(np.diag(P), 1e-12, None)
    loss = float(-np.mean(np.log(diag)))
    return loss, P


def _grad_W_linear_infonce(
    X1: np.ndarray,
    X2: np.ndarray,
    Z1: np.ndarray,
    Z2: np.ndarray,
    P12: np.ndarray,
    tau: float,
    W: np.ndarray,
) -> np.ndarray:
    """
    Gradient approximatif (pédagogique) pour encodeur linéaire normalisé.

    On ignore le terme exact de la normalisation L2 dans le gradient pour garder:
    - simple
    - stable en pratique (avec lr petit)

    Dérivation:
      L = -mean log softmax((z1_i·z2_j)/tau)[j=i]
      dL/dlogits = (P - I)/B
      dlogits/dz1 = (P - I)/B @ z2 / tau
      dlogits/dz2 = (P - I).T/B @ z1 / tau
      z = W x
      dW = sum_i (dz_i outer x_i)
    """
    B = X1.shape[0]
    I = np.eye(B, dtype=np.float32)
    G = (P12 - I).astype(np.float32) / float(B)  # (B,B)

    dz1 = (G @ Z2).astype(np.float32) / float(tau)  # (B,d)
    dz2 = (G.T @ Z1).astype(np.float32) / float(tau)

    # dW = dz^T @ X
    dW1 = dz1.T @ X1.astype(np.float32)  # (d,nf)
    dW2 = dz2.T @ X2.astype(np.float32)
    dW = (dW1 + dW2).astype(np.float32)
    return dW


def entrainer_encodeur_contrastif_v1(
    X: np.ndarray,
    d: int = 16,
    batch: int = 256,
    epochs: int = 10,
    tau: float = 0.2,
    lr: float = 0.25,
    seed: int = 42,
    p_drop: float = 0.15,
    bruit: float = 0.01,
) -> Tuple[EncodeurContrastifV1, Dict]:
    """
    Entraîne un encodeur linéaire W sur un dataset de features X (N,24).
    Retourne (encodeur, stats).
    """
    rng = np.random.default_rng(seed)
    N = int(X.shape[0])
    enc = EncodeurContrastifV1(d=d, n_features=int(X.shape[1]))
    W = enc.W
    assert W is not None

    losses: List[float] = []

    for ep in range(int(epochs)):
        idx = rng.permutation(N)
        Xs = X[idx]
        for i0 in range(0, N, int(batch)):
            xb = Xs[i0 : i0 + int(batch)]
            if xb.shape[0] < 2:
                continue

            # deux vues augmentées
            x1 = np.stack([augmentation_v1(x, rng, p_drop=p_drop, bruit=bruit) for x in xb], axis=0).astype(np.float32)
            x2 = np.stack([augmentation_v1(x, rng, p_drop=p_drop, bruit=bruit) for x in xb], axis=0).astype(np.float32)

            # embeddings
            z1 = enc.encoder_batch(x1)  # (B,d)
            z2 = enc.encoder_batch(x2)

            loss, P12 = _loss_infonce(z1, z2, tau=tau)
            losses.append(float(loss))

            # gradient
            dW = _grad_W_linear_infonce(x1, x2, z1, z2, P12, tau=float(tau), W=W)

            # update SGD
            W -= float(lr) * dW

        enc.W = W

    stats = {
        "d": int(d),
        "n_features": int(X.shape[1]),
        "batch": int(batch),
        "epochs": int(epochs),
        "tau": float(tau),
        "lr": float(lr),
        "seed": int(seed),
        "p_drop": float(p_drop),
        "bruit": float(bruit),
        "loss_mean": float(np.mean(losses)) if losses else None,
        "loss_last": float(losses[-1]) if losses else None,
        "losses": losses[-200:],  # on tronque pour rester léger
        "N": int(N),
    }
    return enc, stats


def charger_features_depuis_jsonl(path: str, limite: Optional[int] = None) -> np.ndarray:
    """
    Lit un jsonl d'événements et produit X (N,24).
    """
    X: List[np.ndarray] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            evt = json.loads(line)
            try:
                feat = features_depuis_evt(evt)
            except Exception:
                continue
            X.append(feat.astype(np.float32))
            if limite is not None and len(X) >= int(limite):
                break
    if not X:
        return np.zeros((0, 96), dtype=np.float32)
    return np.stack(X, axis=0).astype(np.float32)


def kmeans_v1(
    Z: np.ndarray,
    k: int = 512,
    iters: int = 25,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """
    k-means simple (numpy) sur embeddings Z (N,d).
    Retourne (centroides (k,d), labels (N,), stats).
    """
    rng = np.random.default_rng(seed)
    N, d = int(Z.shape[0]), int(Z.shape[1])
    if N == 0:
        return np.zeros((k, d), dtype=np.float32), np.zeros((0,), dtype=np.int32), {"N": 0}

    # init: échantillon aléatoire sans remise
    pick = rng.choice(N, size=min(int(k), N), replace=False)
    C = Z[pick].copy().astype(np.float32)
    if C.shape[0] < int(k):
        # pad si N < k
        pad = np.zeros((int(k) - C.shape[0], d), dtype=np.float32)
        C = np.concatenate([C, pad], axis=0)

    labels = np.zeros((N,), dtype=np.int32)
    inertias: List[float] = []

    for it in range(int(iters)):
        # assign
        # distances au carré via (z-c)^2 = z^2 + c^2 - 2 z·c
        z2 = np.sum(Z * Z, axis=1, keepdims=True)  # (N,1)
        c2 = np.sum(C * C, axis=1, keepdims=True).T  # (1,k)
        dots = Z @ C.T  # (N,k)
        dist2 = z2 + c2 - 2.0 * dots
        labels = np.argmin(dist2, axis=1).astype(np.int32)
        inertia = float(np.mean(np.min(dist2, axis=1)))
        inertias.append(inertia)

        # update
        C_new = np.zeros_like(C)
        counts = np.zeros((int(k),), dtype=np.int32)
        for i in range(N):
            j = int(labels[i])
            C_new[j] += Z[i]
            counts[j] += 1
        for j in range(int(k)):
            if counts[j] > 0:
                C_new[j] /= float(counts[j])
            else:
                # cluster vide: réinit aléatoire
                C_new[j] = Z[int(rng.integers(0, N))]
        C = C_new.astype(np.float32)

    stats = {
        "k": int(k),
        "iters": int(iters),
        "seed": int(seed),
        "N": int(N),
        "d": int(d),
        "inertia_last": float(inertias[-1]) if inertias else None,
        "inertias": inertias[-50:],
    }
    return C, labels.astype(np.int32), stats

