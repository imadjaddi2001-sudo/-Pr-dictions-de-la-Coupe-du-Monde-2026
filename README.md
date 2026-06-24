# ⚽ FIFA World Cup 2026 Predictor

Application web complète de prédiction de la Coupe du Monde 2026.

## 🚀 Lancement rapide

```bash
pip install -r requirements.txt
python app.py
```
L'app s'ouvre automatiquement sur **http://localhost:5000**

## 📋 Fonctionnalités

| Page | Description |
|------|-------------|
| 🏠 Dashboard | Top 5 favoris, statistiques clés, répartition par confédération |
| 📊 Probabilités | Tableau complet des 48 équipes avec probabilités par étape |
| 🔠 Groupes | Visualisation des 12 groupes A→L |
| 🏆 Bracket | Simulation live du tournoi (R32 → Finale) |
| ⚔️ Match | Prédiction tête-à-tête + simulation de groupe |
| 🌍 Classement FIFA | Scraping live de inside.fifa.com |
| 📁 Export CSV | Export de tous les résultats en CSV |

## 📁 Fichiers CSV générés

- `data/processed/group_stage_results.csv` — Classements phase de groupes
- `data/processed/group_matches.csv` — Tous les 72 matchs de groupe
- `data/processed/knockout_results.csv` — Bracket complet (R32 à Finale)
- `data/processed/tournament_probabilities.csv` — Probs Monte Carlo par équipe
- `data/processed/fifa_rankings_snapshot.csv` — Classement FIFA snapshot

## 🔧 Architecture

```
wc2026_predictor/
├── app.py              ← Flask app (API + routes)
├── run.py              ← Lanceur avec auto-install
├── requirements.txt
├── src/
│   ├── scraper.py      ← Scraping FIFA rankings
│   ├── predictor.py    ← Modèle ELO + probabilités
│   └── simulation.py   ← Monte Carlo + export CSV
├── templates/
│   └── index.html      ← App web single-page
└── data/
    ├── raw/            ← Données brutes + cache FIFA
    ├── processed/      ← CSVs exportés
    └── reference/      ← Fixtures, groupes, bracket
```

## 🧠 Modèle

- **ELO ratings** basés sur l'historique de matchs internationaux depuis 1872
- **Win probability** via formule ELO standard (400 points = 10x plus probable)
- **Draw probability** modelisée via facteur logistique
- **Monte Carlo** : N simulations du tournoi complet (configurable)
- **Scraping FIFA** : live depuis inside.fifa.com, fallback cache 24h

## 🌐 API REST

| Endpoint | Description |
|----------|-------------|
| `GET /api/rankings?refresh=true` | Classement FIFA (scraping live) |
| `GET /api/probabilities` | Probs toutes équipes |
| `GET /api/groups` | Composition des 12 groupes |
| `GET /api/predict_match?team_a=X&team_b=Y` | Prédiction H2H |
| `GET /api/simulate_group/<G>` | Simulation groupe A-L |
| `GET /api/simulate_tournament` | Tournoi complet simulé |
| `GET /api/export_csv?n_sim=500` | Lance Monte Carlo + exporte CSVs |

Basé sur les données de [Anas Riad](https://www.linkedin.com/in/riadanas/) — extended & redesigned.
