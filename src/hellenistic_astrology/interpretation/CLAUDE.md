# CLAUDE.md — interpretation/

Assemblage d'un **brief factuel** pour la rédaction assistée de la Phase 3
— Interprétation. Ce module ne rédige rien lui-même : une seule fonction
publique, `build_interpretation_brief(observation, birth, when=None)` dans
`brief.py`.

## Pourquoi ce module existe séparément de `docgen/`

Phase 3 est, dans les deux documents de référence, de la prose
interprétative véritable (« indique une vie construite autour de... »),
pas un gabarit déterministe comme la Phase 2. Décision actée (jalon 26,
validée explicitement avec l'utilisateur) : pas d'appel API automatisé
dans le pipeline (coût, non-reproductibilité, en tension avec l'objectif
« pipeline reproductible » du projet) — la rédaction reste une étape
supervisée, hors CLI, via le skill
`.claude/skills/hellenistic-astrology-phase3/SKILL.md` ou une session
assistée équivalente (Claude Chat, Mistral Le Chat/Vibe).

## Ce que fait `build_interpretation_brief`

Pour chaque sous-section de Phase 3, réutilise au maximum ce que `docgen`
a déjà produit et testé, plutôt que de re-dériver les faits :

| Sous-section | Origine des faits |
|---|---|
| Orientation générale | `docgen.builder.add_elemental_modal_section` + `add_angularity_section` |
| L'Ascendant et son maître | `docgen.builder.add_ascendant_and_ruler_section` |
| Les luminaires | `docgen.builder.add_luminaries_section` |
| La structure du thème | `docgen.builder.add_aspects_section` |
| Nuances de secte/dignité | `docgen.builder.add_dignities_and_receptions_section` + rôle de secte par planète (nouveau, jalon 26) |
| Synthèse | aucun fait neuf — consigne de clôture uniquement |
| Repères temporels actuels | `core.zodiacal_releasing.active_period` sur les chapitres déjà calculés (jalon 18), à la date `when` |
| Limites de cette analyse | précision de l'heure de naissance (`BirthData.local_time`) |

Ces fonctions `docgen` sont rejouées contre un `docx.Document()` jetable et
leur texte de paragraphe est extrait tel quel — **ne pas** dupliquer leur
logique ici : si un fait manque au brief, la correction se fait dans
`docgen/`, pas par un contournement local.

## Contenu volontairement fixe dans le brief

- Le rappel des règles de style de CLAUDE.md (`STYLE_REMINDER`) et la
  bibliographie (`bibliography.REFERENCES`) sont toujours inclus tels
  quels, pour que le brief reste autoportant si collé dans une interface
  qui n'a pas accès à ce dépôt (Claude Chat, Mistral Le Chat).
- Ne jamais ajouter de prose interprétative dans ce module, même à titre
  d'exemple ou de gabarit — ce serait exactement la limite que la
  séparation `docgen`/`interpretation` cherche à maintenir.

## Tests

`tests/test_interpretation_brief.py` vérifie la présence des 8
sous-sections et de la bibliographie, et recoupe des faits déjà validés
par les tests Phase 1/2 (aucune nouvelle affirmation astrologique à
prouver ici — c'est la réutilisation qui est testée, pas l'exactitude des
calculs sous-jacents).

## Historique détaillé

Jalon 26 (`CLAUDE.md` racine, section État d'avancement) pour la décision
de mécanisme et son contexte complet ; jalon 27 pour le skill qui consomme
ce brief ; jalon 28 pour le serveur MCP local
(`generate_interpretation_brief`) qui expose cette même fonction.
