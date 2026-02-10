"""
préparation d'un agent-personne (sai-a107)

module offline : assemble et entraîne un artefact "agent-personne" à partir d'un
catalogue de têtes et d'un tronc, en consommant éventuellement des connaissances
épistémiques (registre) et des épisodes (jsonl).

ce module ne doit pas contenir de logique "tick -> action" (ça, c'est l'agent en arène
conforme à `agent_service.app.contrats_agents.IAgentArene`, orchestré par `runner`).

Usage :
    ui_cli : outils de préparation d'agent (sai-a107)

    commande: ui_cli preparer-agent <sous-commande> ...
"""
