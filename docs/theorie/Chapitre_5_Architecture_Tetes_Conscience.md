# Chapitre 5 --- Architecture des têtes et de la conscience

Version générée le 2026-02-24

------------------------------------------------------------------------

# 1️⃣ Position générale

Après le tronc et le routage attentionnel, il est nécessaire de
formaliser :

-   la structure des têtes spécialisées,
-   leur orchestration par la conscience,
-   leur relation avec les réflexes acquis,
-   leur rôle dans la modification des instruments et de
    l'apprentissage.

Les têtes ne sont pas des encodeurs. Ce sont des modules spécialisés
manipulés par la conscience.

------------------------------------------------------------------------

# I. Activation de la conscience

Le tronc produit une classe de routage :

c_t = Γ(z_t\^{primitive})

Si :

c_t = A

alors la conscience est activée.

La conscience reçoit :

z_t

ainsi que :

-   m_t (mémoire globale)
-   M\_{k,t} (mémoire par canal)

La conscience constitue un espace de travail actif.

------------------------------------------------------------------------

# II. Définition d'une tête

Une tête est un module spécialisé :

T_i : Z × M × O → A\*

où :

-   Z est l'espace latent intégré,
-   M représente les mémoires accessibles,
-   O les objectifs courants,
-   A\* un ensemble d'actions candidates.

Une tête peut produire :

-   un plan d'action,
-   une hypothèse,
-   une évaluation,
-   une simulation.

Les têtes ne modifient pas directement le monde. Elles produisent des
propositions.

------------------------------------------------------------------------

# III. Types de têtes possibles

Exemples de têtes :

1.  Planification
    -   recherche de séquences d'actions
    -   optimisation sous contraintes
2.  Simulation interne
    -   projection s\_{t+k} = f_hat(s_t, A_seq)
3.  Évaluation normative
    -   estimation de valeur
    -   comparaison de scénarios
4.  Abstraction conceptuelle
    -   catégorisation
    -   création de nouvelles représentations
5.  Stratégie instrumentale
    -   modification d'échelle
    -   changement d'instrument
    -   allocation attentionnelle

------------------------------------------------------------------------

# IV. Orchestration par la conscience

La conscience agit comme un orchestrateur :

Omega : (z_t, m_t, objectifs) → sélection de têtes

Elle peut :

-   activer une ou plusieurs têtes,
-   séquencer leur utilisation,
-   interrompre une tête,
-   comparer leurs résultats.

La conscience produit :

A_t\^{plan}

qui est transmis au moteur.

------------------------------------------------------------------------

# V. Relation avec les réflexes acquis

Les automatismes acquis sont définis comme :

A_t\^{auto} = mu(z_t)

Ce sont d'anciens traitements conscients devenus rapides.

La conscience peut :

-   inhiber un automatisme,
-   réentraîner un automatisme,
-   transformer un plan répété en automatisme.

Ainsi :

Automatisme = compression d'anciens traitements conscients.

------------------------------------------------------------------------

# VI. Interaction avec l'apprentissage

Les résultats produits par les têtes peuvent servir de base
à une modification ultérieure des paramètres internes
(encodeurs h_k, fusion H, routage Gamma, réflexes rho, automatismes mu),
mais uniquement en phase d'entraînement.

En situation d’arène, les paramètres sont figés.
Les têtes ne modifient pas les poids.
Elles produisent des propositions, des annotations,
et éventuellement des sujets de réflexion
destinés au registre épistémique.

L'apprentissage agit comme une condensation progressive :

Traitement conscient répété → automatisme.

------------------------------------------------------------------------

# VII. Hiérarchie fonctionnelle

Flux perceptif ↓ Tronc (routage Gamma) ↓ Réflexe / Automatisme /
Attention ↓ (si Attention) ↓ Conscience (Omega) ↓ Têtes spécialisées ↓
Plan ↓ Moteur ↓ Monde

------------------------------------------------------------------------

# VIII. Position théorique adoptée

1.  Le tronc décide de l'activation consciente.
2.  L'attention est une classe de routage.
3.  La conscience est un espace de travail dynamique.
4.  Les têtes sont des modules spécialisés manipulés par la conscience.
5.  Les automatismes sont des condensations de traitements conscients
    passés.

------------------------------------------------------------------------

# Synthèse

L'architecture complète distingue :

-   perception,
-   routage,
-   réflexes,
-   conscience,
-   têtes spécialisées,
-   apprentissage.

La conscience ne perçoit pas directement le monde. Elle manipule des
représentations issues du tronc.

Les têtes sont des instruments cognitifs internes, permettant la
planification, l'abstraction et la stratégie.

Le système évolue par condensation progressive du traitement conscient
vers l'automatisation.
