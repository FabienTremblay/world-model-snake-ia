from __future__ import annotations

from ui_cli.app.evenements.cli_evenements import construire_parser_evenements


def test_cli_evenements_parser_smoke():
    ap = construire_parser_evenements()
    ns = ap.parse_args(["--experience", "X", "--ticks", "3"])
    assert ns.experience == "X"
    assert ns.ticks == 3
