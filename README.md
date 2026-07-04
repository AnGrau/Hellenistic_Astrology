# Hellenistic Astrology

Calcul et mise en forme de thèmes natals en astrologie hellénistique (signes entiers). Voir `CLAUDE.md` pour le contexte complet du projet, les réglages astrologiques et la roadmap.

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

Si `place` est ambigu (ex. `"Paris"` sans indication de pays), la génération échoue avec la liste des lieux candidats trouvés. Ajouter `"country_code": "fr"` (code pays ISO 3166-1 alpha-2) pour lever l'ambiguïté, ou préciser directement `place` (ex. `"Paris, France"`).

Puis générer le document :

```bash
uv run hellenistic-astrology naissance.json
```

Le `.docx` est écrit dans `output/<nom>.docx` par défaut (dossier gitignored, contient des données personnelles), ou vers le chemin donné avec `-o`/`--output`.

Le document généré couvre la Phase 1 complète (Observation : positions — y compris Nœud Nord/Sud et Part d'Éros —, maîtrises traditionnelles, dignités mineures — triplicité, bornes égyptiennes, décans —, aspects par signe, réceptions mutuelles par domicile, libération zodiacale niveaux L1+L2 sur 100 ans depuis la Part de Fortune et la Part de l'Esprit, y compris le relâchement du lien) ainsi que la quasi-totalité de la Phase 2 (Fiche technique : répartition élémentaire et modale, angularité, dignités et réceptions — y compris la combustion « sous les rayons du Soleil » —, Ascendant et son maître, Luminaires — y compris la phase de lunaison natale —, Nœuds et Parts — y compris la configuration d'éclipse) — voir "Reste à faire" dans `CLAUDE.md` pour la Structure du thème et la Phase 3.
