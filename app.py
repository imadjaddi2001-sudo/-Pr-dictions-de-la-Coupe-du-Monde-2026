"""
FIFA World Cup 2026 Predictor — Flask Web Application
Run: python app.py  → opens at http://localhost:5000
"""
import json, sys, logging
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory

# Make src importable
sys.path.insert(0, str(Path(__file__).parent))

from src.scraper import load_or_scrape_rankings
from src.predictor import (
    predict_match_head2head, ELO_RATINGS, GROUPS,
    FIFA_RANKS, CONFEDERATIONS, simulate_match, simulate_group
)
from src.simulation import run_and_export, simulate_full_tournament_once

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates", static_folder="static")
PROCESSED_DIR = Path(__file__).parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Load precomputed probabilities from existing project data
import pandas as pd
_PRECOMP_CSV = Path(__file__).parent / "data" / "processed" / "wc2026_tournament_probabilities.csv"
_precomp_probs = {}
if _PRECOMP_CSV.exists():
    _df = pd.read_csv(_PRECOMP_CSV)
    for _, row in _df.iterrows():
        _precomp_probs[row["team"]] = {
            "R32": row.get("r32_prob", 0), "R16": row.get("r16_prob", 0),
            "QF": row.get("qf_prob", 0), "SF": row.get("sf_prob", 0),
            "Final": row.get("final_prob", 0), "Winner": row.get("winner_prob", 0),
            "elo": row.get("elo", ELO_RATINGS.get(row["team"], 1500)),
            "confederation": row.get("confederation", CONFEDERATIONS.get(row["team"], "")),
            "fifa_rank": row.get("fifa_rank", FIFA_RANKS.get(row["team"], 99)),
        }


@app.route("/")
def indexx():
    return render_template("indexx.html")


@app.route("/api/rankings")
def api_rankings():
    force = request.args.get("refresh", "false").lower() == "true"
    df = load_or_scrape_rankings(force_refresh=force)
    return jsonify({"rankings": df.to_dict("records"), "total": len(df)})


@app.route("/api/probabilities")
def api_probabilities():
    teams = []
    for team, data in _precomp_probs.items():
        teams.append({
            "team": team,
            "fifa_rank": data.get("fifa_rank", FIFA_RANKS.get(team, 99)),
            "elo": round(data.get("elo", ELO_RATINGS.get(team, 1500)), 1),
            "confederation": data.get("confederation", CONFEDERATIONS.get(team, "")),
            "r32": data.get("R32", 0),
            "r16": data.get("R16", 0),
            "qf": data.get("QF", 0),
            "sf": data.get("SF", 0),
            "final": data.get("Final", 0),
            "winner": data.get("Winner", 0),
        })
    teams.sort(key=lambda x: x["winner"], reverse=True)
    return jsonify({"teams": teams})


@app.route("/api/groups")
def api_groups():
    groups_data = {}
    for grp, teams in GROUPS.items():
        groups_data[grp] = [
            {"team": t, "elo": round(ELO_RATINGS.get(t, 1500), 1),
             "rank": FIFA_RANKS.get(t, 99), "confederation": CONFEDERATIONS.get(t, "")}
            for t in teams
        ]
    return jsonify({"groups": groups_data})


@app.route("/api/predict_match")
def api_predict_match():
    team_a = request.args.get("team_a", "")
    team_b = request.args.get("team_b", "")
    if not team_a or not team_b:
        return jsonify({"error": "Provide team_a and team_b"}), 400
    if team_a not in ELO_RATINGS:
        return jsonify({"error": f"Unknown team: {team_a}"}), 404
    if team_b not in ELO_RATINGS:
        return jsonify({"error": f"Unknown team: {team_b}"}), 404
    result = predict_match_head2head(team_a, team_b)
    return jsonify(result)


@app.route("/api/simulate_group/<group_name>")
def api_simulate_group(group_name):
    grp = group_name.upper()
    if grp not in GROUPS:
        return jsonify({"error": f"Unknown group: {grp}"}), 404
    teams = GROUPS[grp]
    df, matches = simulate_group(grp, teams)
    return jsonify({
        "group": grp,
        "standings": df[["team","pts","w","d","l","gf","ga","gd","position"]].to_dict("records"),
        "matches": [{k: v for k, v in m.items() if k != "matches"} for m in matches],
    })


@app.route("/api/simulate_tournament")
def api_simulate_tournament():
    """Run a single live tournament simulation."""
    result = simulate_full_tournament_once()
    # Build a clean bracket response
    bracket = {"group_stage": {}, "knockout": [], "winner": result["winner"]}
    for grp, standings in result["group_stage"].items():
        bracket["group_stage"][grp] = [
            {k: v for k, v in s.items() if k != "matches"} for s in standings
        ]
    for m in result["knockout"]:
        bracket["knockout"].append({
            "round": m["round"],
            "team_a": m["team_a"], "team_b": m["team_b"],
            "p_a_win": m["p_a_win"], "p_b_win": m["p_b_win"],
            "winner": m["simulated_winner"],
        })
    return jsonify(bracket)


@app.route("/api/teams")
def api_teams():
    teams = sorted(ELO_RATINGS.keys())
    return jsonify({"teams": teams})


@app.route("/api/export_csv")
def api_export_csv():
    """Run full simulation and export all CSVs."""
    n_sim = int(request.args.get("n_sim", 200))
    n_sim = min(n_sim, 1000)
    summary = run_and_export(n_sim=n_sim)
    return jsonify({
        "exported_files": summary["exported_files"],
        "winner": summary["single_simulation"]["winner"],
        "message": f"Simulation complete ({n_sim} runs). CSVs saved.",
    })


@app.route("/data/processed/<filename>")
def serve_csv(filename):
    return send_from_directory(str(PROCESSED_DIR), filename)


if __name__ == "__main__":
    import webbrowser, threading
    def open_browser():
        import time; time.sleep(1.2)
        webbrowser.open("http://localhost:5000")
    threading.Thread(target=open_browser, daemon=True).start()
    print("\n🏆  WC 2026 Predictor → http://localhost:5000\n")
    app.run(debug=False, port=5000, host="0.0.0.0")
