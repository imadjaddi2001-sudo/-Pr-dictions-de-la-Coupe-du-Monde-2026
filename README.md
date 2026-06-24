# 🏆 FIFA World Cup 2026 Predictor

Application web complète de prédiction de la Coupe du Monde 2026.

## 🚀 Lancement rapide

```bash
pip install -r requirements.txt
python app.py
```

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
- **Monte Carlo** : N simulations du tournoi complet 



