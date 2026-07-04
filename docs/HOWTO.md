# Guide pas à pas : produire une analyse de thème natal

Ce guide part de zéro (dépôt cloné, rien installé) et va jusqu'au document
final. Voir `README.md` pour la référence détaillée de chaque commande, et
`CLAUDE.md` pour le contexte du projet et les réglages astrologiques.

Trois façons d'utiliser ce projet, du plus simple au plus intégré :

- **A. En ligne de commande**, seul, sans assistant IA.
- **B. Depuis Claude Code ou Mistral Vibe**, en travaillant directement dans ce dépôt (le serveur MCP et le skill sont disponibles automatiquement).
- **C. Depuis Claude Chat ou Mistral Le Chat**, sans logiciel local (voir les limites en fin de guide).

Dans les trois cas, le skill `.claude/skills/hellenistic-astrology/` peut guider les étapes 1 à 5 ci-dessous de bout en bout — il appelle les outils MCP quand ils sont disponibles (voies A/B) ou indique la commande exacte à lancer soi-même sinon (voie C), sans jamais sauter la relecture humaine de la Phase 3 (étape 4). Les sous-sections suivantes détaillent chaque étape pour qui préfère la main sur chaque commande.

## 1. Installer

```bash
uv sync
```

Optionnel, pour la précision complète du Swiss Ephemeris (sinon repli
automatique sur la théorie Moshier, précision ~1 arcseconde — largement
suffisante pour une lecture) :

```bash
uv run python scripts/fetch_ephemeris.py
```

## 2. Préparer les données de naissance

Créer un fichier JSON, par exemple `naissance.json` :

```json
{
  "name": "Prénom Nom",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "local_date": "1990-06-15",
  "local_time": "12:00:00",
  "tz_name": "Europe/Paris"
}
```

- Naissance avant 1916 : remplacer `local_date`/`local_time`/`tz_name` par `utc_datetime` (ex. `"1900-01-01T11:00:00+00:00"`).
- Coordonnées inconnues : remplacer `latitude`/`longitude` par `"place": "Paris 14e, France"` (envoie ce texte à un service de géocodage tiers, Nominatim/OpenStreetMap — à n'utiliser qu'en connaissance de cause). Ajouter `"country_code": "fr"` si le lieu est ambigu.

## 3A. Voie ligne de commande

Générer le document Phase 1 + Phase 2 (`.docx`) :

```bash
uv run hellenistic-astrology naissance.json
```

Écrit dans `output/<nom>.docx` par défaut (dossier gitignored). Le document
inclut une page de garde avec la roue du thème, une table des matières,
ainsi que des graphiques (élément/modalité, frise de libération zodiacale)
et un aspectarian planète × planète — voir `README.md` pour le détail.

Générer le brief factuel pour la Phase 3 (nécessaire avant de rédiger
l'Interprétation — voir étape 4) :

```bash
uv run python -c "
import json
from hellenistic_astrology.core.chart import build_observation
from hellenistic_astrology.core.timezone import birth_data_from_dict
from hellenistic_astrology.interpretation.brief import build_interpretation_brief

data = json.load(open('naissance.json'))
birth = birth_data_from_dict(data)
observation = build_observation(birth)
print(build_interpretation_brief(observation, birth))
" > brief.md
```

(Pour les deux thèmes de test du projet uniquement, `scripts/generate_docx.py` et `scripts/generate_brief.py` font la même chose en une commande — voir `README.md`.)

## 3B. Voie Claude Code / Mistral Vibe

En travaillant dans ce dépôt, le serveur MCP (`.mcp.json`, déjà committé)
expose trois outils équivalents à l'étape 3A, sans quitter la
conversation :

- `compute_observation` — renvoie les faits en JSON structuré (pour poser des questions ponctuelles sur le thème sans générer de document).
- `generate_document` — génère le `.docx` complet.
- `generate_interpretation_brief` — génère le brief de Phase 3 directement (équivalent à la commande de l'étape 3A, sans avoir à l'écrire).

Demander simplement, par exemple : *« Génère le brief de Phase 3 pour ces
données de naissance : {...} »* — l'agent appelle l'outil MCP approprié.

## 3C. Voie Claude Chat / Mistral Le Chat (sans logiciel local)

Ces interfaces ne peuvent pas exécuter le calcul elles-mêmes (le serveur
MCP est volontairement local uniquement, voir `README.md` et `CLAUDE.md`
pour la raison — licence Swiss Ephemeris). Générer le brief via 3A ou 3B
d'abord, puis coller son contenu dans la conversation à l'étape 4.

## 4. Rédiger la Phase 3 — Interprétation

Le brief de l'étape précédente contient tous les faits (dignités, aspects,
secte, libération zodiacale...) et les règles de style à respecter, mais
pas la prose elle-même : c'est une rédaction assistée, volontairement
supervisée, pas un rendu automatique.

- **Claude Code** : le skill `.claude/skills/hellenistic-astrology-phase3/` se déclenche automatiquement en fournissant le brief (généré à l'étape 3A ou 3B) — demander directement *« rédige la Phase 3 à partir de ce brief »*.
- **Claude Chat / Mistral Le Chat / Vibe** : coller le contenu du brief dans la conversation avec une demande similaire ; le skill fonctionne à l'identique une fois copié dans le dossier de skills de l'outil utilisé (voir `README.md`, section Skill).

Le résultat est un brouillon à relire : chaque affirmation technique doit
rester vérifiable depuis le brief (voir les règles de style dans le brief
lui-même et dans `CLAUDE.md`). **Finaliser ce texte avant l'étape
suivante** (relire, éditer dans le chat ou directement dans le fichier
`.md`) — l'assemblage ne relit ni ne corrige le contenu, il ne fait que le
mettre en forme dans le document.

## 5. Assembler le document final

Une fois la Phase 3 finalisée, la coller à la suite du `.docx` de Phase
1/2 (étape 3) :

```bash
uv run python scripts/assemble_document.py output/naissance.docx output/naissance_phase3.md
```

Écrit par défaut vers `<docx>_final.docx`, sans jamais modifier le `.docx`
d'entrée. Même opération disponible comme outil MCP
(`assemble_final_document`) depuis Claude Code/Vibe — voir `README.md`.
