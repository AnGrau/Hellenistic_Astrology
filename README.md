# Hellenistic Astrology

Calcul et mise en forme de thèmes natals en astrologie hellénistique (signes entiers). Voir `CLAUDE.md` pour le contexte complet du projet, les réglages astrologiques et la roadmap, et [`docs/HOWTO.md`](docs/HOWTO.md) pour un guide pas à pas (installation → thème → brief → rédaction assistée). [`docs/codebase_reference_review.html`](docs/codebase_reference_review.html) est une référence technique fichier par fichier et une revue de code — instantané à une date donnée (jalon 38), pas une documentation vivante comme `CLAUDE.md`.

## Intentions

Au-delà du thème natal lui-même, ce projet sert aussi de terrain d'expérimentation pour :

- tester Claude Code sur un projet réel, de bout en bout ;
- tester des workflows agentiques (planification, questions de cadrage, itération) ;
- tester les mécanismes d'extension de Claude — Skills, plugins, MCP — voir `.claude/skills/`, `.mcp.json` ;
- le tout appliqué à un sujet volontairement choisi hors du champ professionnel/industrie habituel.

## Installation

```bash
uv sync
```

Optionnel, pour la précision complète du Swiss Ephemeris (sinon repli automatique sur la théorie Moshier) :

```bash
uv run python scripts/fetch_ephemeris.py
```

## Utilisation

Créer un fichier JSON avec les données de naissance :

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

Pour une naissance antérieure à 1916 (résolution automatique du fuseau non fiable), remplacer `local_date`/`local_time`/`tz_name` par `utc_datetime` (ex. `"1900-01-01T11:00:00+00:00"`).

Si tu ne connais pas les coordonnées exactes, remplacer `latitude`/`longitude` par `"place": "Paris 14e, France"` : le lieu est alors résolu via géocodage (Nominatim/OpenStreetMap). **Ceci envoie le texte du lieu sur le réseau à un service tiers** — n'utiliser cette option qu'en connaissance de cause ; fournir directement `latitude`/`longitude` reste le seul mode qui n'envoie aucune donnée nulle part.

Si `place` est ambigu (ex. `"Paris"` sans indication de pays), la génération échoue avec la liste des lieux candidats trouvés. Ajouter `"country_code": "fr"` (code pays ISO 3166-1 alpha-2) pour lever l'ambiguïté, ou préciser directement `place` (ex. `"Paris, France"`). `country_code` ne suffit pas toujours : si Nominatim renvoie plusieurs entrées déjà dans le même pays (rencontré en pratique avec `"Villeneuve-sur-Lot, France"`, qui renvoie deux entrées OSM distinctes — avec et sans code postal), ajouter le code postal directement dans `place` (ex. `"Villeneuve-sur-Lot, 47300, France"`).

Puis générer le document :

```bash
uv run hellenistic-astrology naissance.json
```

Le `.docx` est écrit dans `output/<nom>.docx` par défaut (dossier gitignored, contient des données personnelles), ou vers le chemin donné avec `-o`/`--output`.

Le document généré couvre la Phase 1 complète (Observation : positions — y compris Nœud Nord/Sud et Part d'Éros —, maîtrises traditionnelles, dignités mineures — triplicité, bornes égyptiennes, décans —, aspects par signe, aspectarian planète × planète, réceptions mutuelles par domicile, libération zodiacale niveaux L1+L2 sur 100 ans depuis la Part de Fortune et la Part de l'Esprit, y compris le relâchement du lien) ainsi que la Phase 2 complète (Fiche technique : répartition élémentaire et modale, angularité, dignités et réceptions — y compris la combustion « sous les rayons du Soleil » —, Ascendant et son maître, Luminaires — y compris la phase de lunaison natale —, Nœuds et Parts — y compris la configuration d'éclipse, Condition planétaire — bonification/corruption par aspect, enclosure par signe, phénomènes solaires imbriqués cazimi/combustion/sous les rayons, classement à 6 niveaux des 7 planètes classiques).

Le document commence par une page de garde (nom, Ascendant, secte, roue du thème) et une table des matières, et intègre plusieurs visuels générés directement depuis les données calculées (jamais un second moteur de calcul indépendant — voir `CLAUDE.md`, jalon 33) : la roue du thème avec ses lignes d'aspect, un graphique à barres élément/modalité, une frise chronologique de la libération zodiacale, ainsi que des cellules colorées selon la dignité essentielle dans la table des positions. La table des matières est un champ Word natif (`TOC`) : ouvrir le document dans Word/LibreOffice peuple les numéros de page automatiquement (ou clic-droit → Mettre à jour le champ si besoin).

La Phase 3 (Interprétation) n'est pas encore automatisée dans le CLI : `hellenistic_astrology.interpretation.brief.build_interpretation_brief()` assemble un brief factuel déterministe (réutilisant les faits déjà calculés en Phase 1/2, plus la période de libération zodiacale active aujourd'hui) destiné à une rédaction assistée hors CLI, pas à un rendu automatique.

Un skill Claude Code (`.claude/skills/hellenistic-astrology-phase3/`) rédige cette Phase 3 à partir d'un brief déjà généré, en respectant les règles de style du projet et en restant traçable aux faits fournis. Il suit le standard ouvert [Agent Skills](https://agentskills.io) et fonctionne aussi sur Claude.ai/Claude Chat et Mistral Vibe (une fois copié ou référencé dans leur propre dossier de skills) — voir "Reste à faire" dans `CLAUDE.md` pour la suite.

Un second skill (`.claude/skills/hellenistic-astrology/`) orchestre les quatre étapes de bout en bout (calcul, brief, rédaction, assemblage) à partir de simples données de naissance, en s'adaptant à ce que l'environnement courant peut exécuter : appel direct des outils MCP ci-dessous quand ils sont disponibles (Claude Code, Claude Desktop, Mistral Vibe), ou instructions de commande à lancer soi-même sinon (Claude Chat, Mistral Le Chat). La relecture humaine de la Phase 3 reste, dans les deux cas, une étape obligatoire que ce skill ne saute jamais.

## Serveur MCP local

Un serveur MCP local (`src/hellenistic_astrology/mcp_server.py`, transport stdio — sous-processus local, aucune exposition réseau) expose quatre outils à Claude Code et Mistral Vibe quand ils travaillent sur ce dépôt cloné : `compute_observation` (JSON structuré), `generate_document` (`.docx` complet), `generate_interpretation_brief` (brief de Phase 3) et `assemble_final_document` (ajoute la prose de Phase 3, une fois rédigée et finalisée, à la suite du `.docx` — voir "Assembler le document final" ci-dessous).

- **Claude Code** : rien à faire, `.mcp.json` est déjà committé à la racine du dépôt ; approuver le serveur au premier lancement (`claude mcp list` pour vérifier son statut).
- **Claude Desktop** (testé avec succès en conditions réelles, Windows + WSL2) : Claude Desktop ne découvre pas `.mcp.json` automatiquement (contrairement à Claude Code) — il faut l'ajouter à sa propre config globale, **Réglages → Développeur → Modifier la config** (fichier `%APPDATA%\Claude\claude_desktop_config.json` sur Windows). Depuis un poste Windows dont le dépôt vit dans WSL2, le serveur doit être lancé via `wsl.exe` :
  ```json
  {
    "mcpServers": {
      "hellenistic-astrology": {
        "command": "wsl.exe",
        "args": [
          "-d", "Ubuntu",
          "--",
          "bash", "-lc",
          "cd /chemin/vers/Hellenistic_Astrology && /chemin/vers/uv run python -m hellenistic_astrology.mcp_server"
        ]
      }
    }
  }
  ```
  Remplacer `-d Ubuntu` par le nom de la distribution WSL utilisée, et les deux chemins par les chemins réels (utiliser le chemin absolu de `uv`, ex. via `which uv` dans WSL — un process lancé par une appli graphique n'hérite pas toujours du `PATH` du shell interactif). Le `cd` est nécessaire : `uv run` doit trouver `pyproject.toml` dans le répertoire courant.

  **Piège rencontré en pratique** : `mcpServers` doit être une clé à la **racine** du fichier JSON (au même niveau que les autres réglages globaux de l'application), pas nichée à l'intérieur d'un objet de préférences existant (ex. `preferences.epitaxyPrefs`) — facile à rater en éditant à la main un fichier de config déjà volumineux. Après modification, quitter complètement Claude Desktop (pas juste fermer la fenêtre) et le relancer pour que le nouveau serveur apparaisse dans **Réglages → Serveurs MCP locaux**.
- **Mistral Vibe** : ajouter la même commande (`uv run --directory <chemin-du-dépôt> python -m hellenistic_astrology.mcp_server`) dans sa propre configuration de serveurs MCP locaux (voir sa documentation — pas de fichier de config Vibe committé ici).

Ce serveur reste volontairement **local uniquement** : un serveur MCP hébergé publiquement (pour Claude Chat ou Mistral Le Chat directement, sans logiciel local) est hors périmètre pour l'instant, car il déclencherait la clause de licence Swiss Ephemeris Professional déjà notée dans `CLAUDE.md` (section Environnement de travail).

## Skills dans Claude Desktop

Contrairement à Claude Code (découverte automatique de `.claude/skills/` à la racine du dépôt), **Claude Desktop ne lit jamais ce dossier directement** : les deux skills doivent être importés manuellement, une fois par compte, indépendamment du dépôt Git.

1. **Réglages → Capacités** : activer **« Exécution de code »** (prérequis obligatoire avant de pouvoir importer un skill).
2. **Personnaliser → Skills → « + »  → « Créer un skill » → « Importer un skill »**.
3. Compresser chaque dossier de skill en `.zip` et l'importer séparément :
   - `.claude/skills/hellenistic-astrology/` → `hellenistic-astrology.zip`
   - `.claude/skills/hellenistic-astrology-phase3/` → `hellenistic-astrology-phase3.zip`
4. Activer les deux dans le même panneau **Personnaliser → Skills**.

**Importer les deux skills, pas seulement celui de bout en bout** : l'étape 3 du skill `hellenistic-astrology` renvoie explicitement aux règles de rédaction du skill `hellenistic-astrology-phase3` (« ne pas dupliquer ces règles ici ») — cette référence ne se résout que si les deux sont importés.

Cet import reste **propre au compte**, séparé du dépôt : toute modification future d'un `SKILL.md` nécessite de recompresser et de réimporter manuellement, rien ne synchronise automatiquement les deux.

Une fois les deux skills importés/activés **et** le serveur MCP local connecté (section ci-dessus), invoquer le skill `hellenistic-astrology` dans une conversation Claude Desktop appelle directement les quatre outils MCP à chaque étape, exactement comme dans Claude Code — la relecture humaine de la Phase 3 restant, dans tous les cas, une étape obligatoire jamais sautée. Si le serveur MCP n'est pas connecté, le skill retombe sur son mode « sans outils » : il indique la commande CLI exacte à lancer soi-même dans un vrai terminal sur le dépôt cloné (l'exécution de code de Claude Desktop est un bac à sable isolé, sans accès à ce dépôt).

## Assembler le document final

Une fois la Phase 3 rédigée et **finalisée** (relue/éditée dans le chat ou dans son fichier `.md` — pas avant), l'ajouter à la suite du `.docx` de Phase 1/2 déjà généré :

```bash
uv run python scripts/assemble_document.py output/anthony.docx output/anthony_phase3_draft.md
```

Écrit par défaut vers `<docx>_final.docx` (ex. `output/anthony_final.docx`) — **ne modifie jamais le `.docx` d'entrée**. Chemin de sortie personnalisable avec `-o`/`--output`. Même opération disponible comme outil MCP (`assemble_final_document`, voir ci-dessus) depuis Claude Code/Vibe.

Le texte Markdown est traité tel quel (titres `#`/`##`, paragraphes, puces `- `, emphase `*texte*`) — c'est pourquoi la finalisation doit précéder l'assemblage : ce script ne relit ni ne corrige le contenu, il ne fait que le mettre en forme dans le document.

## Licence

AGPL-3.0-or-later (voir [`LICENSE`](LICENSE)) — ce dépôt importe directement `pyswisseph` (Swiss Ephemeris), lui-même sous AGPL-3.0 ; distribuer ce code sous une licence compatible s'impose donc aussi, indépendamment de toute question de service réseau. Voir `CLAUDE.md`, section Environnement de travail, pour le détail (dont la distinction avec la clause spécifique à l'AGPL sur les services hébergés publiquement, qui reste une question séparée et non engagée).
