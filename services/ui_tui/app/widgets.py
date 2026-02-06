from __future__ import annotations

from textual.widgets import Static

class Grille(Static):
    """Affiche le rendu ASCII déjà produit par les observations du bus."""

    def __init__(self, get_obs, **kwargs) -> None:
        super().__init__(**kwargs)
        self.get_obs = get_obs

    def texte(self) -> str:
        obs = self.get_obs()
        if obs is None:
            return "(en attente...)"
        rendu = getattr(obs, "rendu_debug", None)
        if not rendu:
            return "(aucun rendu_debug)"
        return "\n".join(rendu)

class Bandeau(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._msg = ""

    def set_msg(self, msg: str) -> None:
        self._msg = msg
        self.update(msg)

class PanneauAide(Static):
    def render_aide(self) -> str:
        return (
            "Touches: flèches=agir | p=play/pause | s=step | r=reset | "
            "j=journal | t=stats | esc=menu | q=quit"
        )

    def on_mount(self) -> None:
        self.update(self.render_aide())
