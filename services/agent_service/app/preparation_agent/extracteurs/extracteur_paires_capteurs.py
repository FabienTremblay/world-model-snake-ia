"""
Extracteur de paires capteurs depuis journal JSONL.

Ce module extrait des paires (capteurs_t, capteurs_t+1) depuis un journal
d'épisodes pour construire un dataset supervisé d'apprentissage.

Alignement théorique:
- Chapitre 2: Traitement des observations instrumentales
- Chapitre 3: Encodage des états en représentations compréhensibles
- Chapitre 4: Préparation des données pour le tronc
"""

import json
import base64
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List
import torch


class ExtracteurPairesCapteurs:
    """
    Extrait des paires (capteurs_t, capteurs_t+1) depuis un journal JSONL.
    
    Rôle:
        Transformer un journal d'épisodes (format JSONL) en dataset
        supervisé pour entraîner un modèle prédictif.
    
    Théorie (Chapitre 2):
        Les capteurs sont des projections instrumentales:
            oₜ = g(sₜ, i)
        
        L'extracteur construit les paires de transitions observées:
            (oₜ, oₜ₊₁)
        
        Ces paires permettent d'apprendre un modèle interne:
            f̂: oₜ → ôₜ₊₁
    
    Format des capteurs (JEPA-1):
        - Encodage: base64 (chaîne de caractères)
        - Décodage: bytes → float vector normalisé [0, 1]
        - Dimension: 560 (pad/truncate)
        
        Avantage vs hash:
            - Préserve plus d'information structurelle
            - Distance euclidienne significative
            - Compatible avec réseaux de neurones
    """
    
    def __init__(self, dim_vecteur: int = 560):
        """
        Initialiser l'extracteur.
        
        Args:
            dim_vecteur: Dimension cible des vecteurs capteurs
        
        Note:
            560 est la dimension utilisée dans JEPA-1 pour capteurs_compact.
            Cette dimension peut être ajustée selon le type d'observations.
        """
        self.dim_vecteur = dim_vecteur
    
    def decoder_capteurs_base64(self, capteurs_compact: str) -> torch.Tensor:
        """
        Décoder une chaîne base64 en vecteur float normalisé.
        
        Args:
            capteurs_compact: Chaîne base64 encodant les capteurs
        
        Returns:
            Vecteur float [dim_vecteur] normalisé dans [0, 1]
        
        Pipeline:
            1. base64 decode → bytes
            2. bytes → float (normalisation byte/255.0)
            3. pad ou truncate → dimension fixe
        
        Théorie:
            Cette transformation préserve l'information tout en
            créant une représentation compatible avec les réseaux
            de neurones.
            
            La normalisation [0, 1] stabilise l'entraînement.
        """
        try:
            bytes_data = base64.b64decode(capteurs_compact)
        except Exception:
            # Fallback: vecteur nul si décodage échoue
            return torch.zeros(self.dim_vecteur, dtype=torch.float32)
        
        # Convertir bytes → float normalisé [0, 1]
        arr = torch.tensor(
            [b / 255.0 for b in bytes_data], 
            dtype=torch.float32
        )
        
        # Pad ou truncate à la dimension cible
        if arr.shape[0] < self.dim_vecteur:
            # Padding avec zéros
            padding = torch.zeros(self.dim_vecteur - arr.shape[0])
            arr = torch.cat([arr, padding])
        elif arr.shape[0] > self.dim_vecteur:
            # Truncation
            arr = arr[:self.dim_vecteur]
        
        return arr
    
    def extraire_depuis_journal(
        self, 
        journal_path: str,
        cle_capteurs: str = "capteurs_compact",
        cle_episode_id: str = "episode_id"
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Extraire les paires (x_t, x_t+1) depuis un journal JSONL.
        
        Args:
            journal_path: Chemin du fichier JSONL
            cle_capteurs: Clé JSON contenant les capteurs encodés
        
        Returns:
            (x, y) où:
                x: [N, dim_vecteur] capteurs au temps t
                y: [N, dim_vecteur] capteurs au temps t+1
        
        Format du journal:
            Chaque ligne est un JSON contenant au minimum:
                {"capteurs_compact": "...base64...", ...}
        
        Théorie:
            Construction du dataset supervisé pour apprendre:
                f̂: zₜ → ẑₜ₊₁
            
            Chaque paire (x[i], y[i]) représente une transition
            observée dans le monde.
        
        Raises:
            ValueError: Si moins de 2 observations dans le journal
        """
        # IMPORTANT (non-régression JEPA-1):
        # - On ne doit JAMAIS créer une paire (t -> t+1) qui traverse une frontière d'épisode.
        # - L'ancien extracteur respectait implicitement cette norme.
        observations: List[torch.Tensor] = []
        episode_ids: List[Any] = []
        
        with open(journal_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    ligne = json.loads(line.strip())
                    capteurs_str = ligne.get(cle_capteurs, "")
                    if capteurs_str:
                        vec = self.decoder_capteurs_base64(capteurs_str)
                        observations.append(vec)
                        episode_ids.append(ligne.get(cle_episode_id))
                except json.JSONDecodeError:
                    # Ignorer les lignes malformées
                    continue
        
        if len(observations) < 2:
            raise ValueError(
                f"Pas assez d'observations dans {journal_path}. "
                f"Trouvé: {len(observations)}, minimum requis: 2"
            )
        
        # Créer les paires (t → t+1)
        # Créer les paires (t → t+1) en respectant les frontières d'épisode.
        x_list: List[torch.Tensor] = []
        y_list: List[torch.Tensor] = []
        for i in range(len(observations) - 1):
            ep_i = episode_ids[i]
            ep_j = episode_ids[i + 1]
            # Si episode_id est absent, on reste conservateur:
            # - Si les deux sont None, on accepte.
            # - Sinon, on coupe la chaîne (pas de paire).
            if ep_i != ep_j and not (ep_i is None and ep_j is None):
                continue
            x_list.append(observations[i])
            y_list.append(observations[i + 1])

        if len(x_list) < 1:
            raise ValueError(
                f"Pas assez de paires dans {journal_path} après filtrage par épisodes. "
                f"Trouvé: {len(x_list)}, minimum requis: 1"
            )
        
        x = torch.stack(x_list)
        y = torch.stack(y_list)
        
        return x, y
    
    def sauvegarder_paires(
        self, 
        x: torch.Tensor, 
        y: torch.Tensor, 
        output_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Sauvegarder les paires au format .pt (PyTorch).
        
        Args:
            x: Observations au temps t [N, dim_vecteur]
            y: Observations au temps t+1 [N, dim_vecteur]
            output_path: Chemin de sauvegarde
            metadata: Métadonnées optionnelles
        
        Format du fichier:
            {
                'x': torch.Tensor,
                'y': torch.Tensor,
                'dim_vecteur': int,
                'metadata': dict (optionnel)
            }
        """

        # IMPORTANT (non-régression):
        # Le format "old" attendu par les tests JEPA-1 est:
        #   {"x": ..., "y": ..., "meta": {...}}
        # On conserve aussi "metadata"/"dim_vecteur" pour compat interne, si besoin.
        save_dict = {'x': x, 'y': y}
        if metadata:
            save_dict['meta'] = metadata      # format old
            save_dict['metadata'] = metadata  # compat existante
        save_dict['dim_vecteur'] = self.dim_vecteur
        
        # Créer le répertoire parent si nécessaire
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        torch.save(save_dict, output_path)
    
    @staticmethod
    def charger_paires(
        path: str
    ) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, Any]]:
        """
        Charger les paires depuis un fichier .pt.
        
        Args:
            path: Chemin du fichier
        
        Returns:
            (x, y, metadata) où:
                x: Observations au temps t
                y: Observations au temps t+1
                metadata: Métadonnées associées (ou {} si absent)
        """
        obj = torch.load(path, map_location='cpu')
        # Compat: certains fichiers contiennent 'meta' (old), d'autres 'metadata' (new).
        meta = obj.get('meta', obj.get('metadata', {}))
        return obj['x'], obj['y'], meta
    
    def extraire_et_sauvegarder(
        self,
        journal_path: str,
        output_path: str,
        cle_capteurs: str = "capteurs_compact",
        cle_episode_id: str = "episode_id",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Pipeline complet: extraire depuis journal et sauvegarder.
        
        Args:
            journal_path: Chemin du journal JSONL
            output_path: Chemin de sauvegarde des paires
            cle_capteurs: Clé JSON des capteurs
            metadata: Métadonnées optionnelles
        
        Returns:
            Statistiques d'extraction:
                - nb_paires: nombre de paires extraites
                - dim_vecteur: dimension des vecteurs
                - journal_path: chemin source
                - output_path: chemin destination
        """
        x, y = self.extraire_depuis_journal(
            journal_path,
            cle_capteurs=cle_capteurs,
            cle_episode_id=cle_episode_id
        )
        
        # Enrichir métadonnées (format old JEPA-1)
        meta = dict(metadata or {})
        meta.update({
            'source_journal': str(journal_path),
            'champ_capteurs': cle_capteurs,
            'dim': self.dim_vecteur,
            'nb_paires': int(x.shape[0]),
            # NOTE: si tu veux coller au meta "old" que tu avais observé:
            # 'mode_string': 'base64_bytes',
            # 'n_grams': 3,
        })
        
        self.sauvegarder_paires(x, y, output_path, meta)
        
        return {
            'nb_paires': x.shape[0],
            'dim_vecteur': self.dim_vecteur,
            'journal_path': str(journal_path),
            'output_path': str(output_path),
        }
    
    def __repr__(self) -> str:
        return f"ExtracteurPairesCapteurs(dim_vecteur={self.dim_vecteur})"


# Fonction utilitaire pour usage CLI
def extraire_paires_cli(
    journal_path: str,
    output_path: str,
    dim_vecteur: int = 560,
    cle_capteurs: str = "capteurs_compact"
) -> None:
    """
    Fonction CLI pour extraction de paires.
    
    Usage:
        from extracteur_paires_capteurs import extraire_paires_cli
        
        extraire_paires_cli(
            "journal_episodes.jsonl",
            "paires_capteurs.pt"
        )
    """
    extracteur = ExtracteurPairesCapteurs(dim_vecteur)
    stats = extracteur.extraire_et_sauvegarder(
        journal_path,
        output_path,
        cle_capteurs
    )
    
    print(f"✓ Extraction réussie:")
    print(f"  - Paires extraites: {stats['nb_paires']}")
    print(f"  - Dimension: {stats['dim_vecteur']}")
    print(f"  - Sauvegardé: {stats['output_path']}")
