"""
Tournament simulation engine — runs group stage + knockout and exports CSVs.
"""
import random, logging
from pathlib import Path
import pandas as pd
from src.predictor import (
    GROUPS, simulate_group, simulate_knockout_match,
    get_best_thirds, predict_match_head2head, ELO_RATINGS,
    FIFA_RANKS, CONFEDERATIONS, run_full_tournament
)

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PROCESSED_DIR = DATA_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def simulate_full_tournament_once() -> dict:
    """Single deterministic simulation. Returns complete bracket results."""
    results = {"group_stage": {}, "knockout": [], "winner": None}

    all_standings = {}
    direct_qualifiers = {}
    all_group_matches = []

    for grp, teams in GROUPS.items():
        df_grp, matches = simulate_group(grp, teams)
        all_standings[grp] = df_grp
        direct_qualifiers[f"1{grp}"] = df_grp[df_grp["position"] == 1].iloc[0]["team"]
        direct_qualifiers[f"2{grp}"] = df_grp[df_grp["position"] == 2].iloc[0]["team"]
        results["group_stage"][grp] = df_grp.to_dict("records")
        for m in matches:
            m["group"] = grp
            all_group_matches.append(m)

    best_thirds = get_best_thirds(all_standings)
    third_teams = [t["team"] for t in best_thirds]
    r32_qualifiers = list(direct_qualifiers.values()) + third_teams

    # Build bracket
    rounds = [
        ("Round of 32", r32_qualifiers),
    ]
    current = r32_qualifiers
    round_names = ["Round of 32", "Round of 16", "Quarter-Finals", "Semi-Finals", "Final"]
    ko_matches = []

    for rname in round_names:
        if len(current) < 2:
            break
        next_round = []
        for i in range(0, len(current) - 1, 2):
            ta, tb = current[i], current[i + 1]
            winner = simulate_knockout_match(ta, tb)
            m = predict_match_head2head(ta, tb)
            m["round"] = rname
            m["simulated_winner"] = winner
            ko_matches.append(m)
            next_round.append(winner)
        current = next_round

    results["knockout"] = ko_matches
    results["winner"] = current[0] if current else None
    results["group_matches"] = all_group_matches
    results["best_thirds"] = best_thirds
    return results


def export_group_stage_csv(results: dict) -> Path:
    rows = []
    for grp, standings in results["group_stage"].items():
        for row in standings:
            row["group"] = grp
            rows.append(row)
    df = pd.DataFrame(rows)
    path = PROCESSED_DIR / "group_stage_results.csv"
    df.to_csv(path, index=False)
    logger.info("Saved group stage to %s", path)
    return path


def export_group_matches_csv(results: dict) -> Path:
    rows = []
    for m in results.get("group_matches", []):
        rows.append({
            "group": m.get("group",""),
            "team_a": m["team_a"], "team_b": m["team_b"],
            "score_a": m["score_a"], "score_b": m["score_b"],
            "outcome": m["outcome"],
            "p_a_win": m["p_a_win"], "p_draw": m["p_draw"], "p_b_win": m["p_b_win"],
        })
    df = pd.DataFrame(rows)
    path = PROCESSED_DIR / "group_matches.csv"
    df.to_csv(path, index=False)
    return path


def export_knockout_csv(results: dict) -> Path:
    rows = []
    for m in results["knockout"]:
        rows.append({
            "round": m["round"],
            "team_a": m["team_a"], "team_b": m["team_b"],
            "p_a_win": m["p_a_win"], "p_draw": m["p_draw"], "p_b_win": m["p_b_win"],
            "simulated_winner": m["simulated_winner"],
            "elo_a": m["elo_a"], "elo_b": m["elo_b"],
        })
    df = pd.DataFrame(rows)
    path = PROCESSED_DIR / "knockout_results.csv"
    df.to_csv(path, index=False)
    return path


def export_probabilities_csv(probs: dict) -> Path:
    rows = []
    for team, stages in probs.items():
        row = {"team": team, "fifa_rank": FIFA_RANKS.get(team, 99),
               "confederation": CONFEDERATIONS.get(team, ""), "elo": ELO_RATINGS.get(team, 1500)}
        row.update(stages)
        rows.append(row)
    df = pd.DataFrame(rows).sort_values("Winner", ascending=False)
    path = PROCESSED_DIR / "tournament_probabilities.csv"
    df.to_csv(path, index=False)
    return path


def export_rankings_csv(df_rankings: pd.DataFrame) -> Path:
    path = PROCESSED_DIR / "fifa_rankings_snapshot.csv"
    df_rankings.to_csv(path, index=False)
    return path


def run_and_export(n_sim: int = 500) -> dict:
    """Run full simulation pipeline and export all CSVs. Returns summary."""
    logger.info("Running single tournament simulation...")
    single = simulate_full_tournament_once()

    logger.info("Running %d Monte Carlo simulations...", n_sim)
    probs = run_full_tournament(n_sim)

    paths = {
        "group_stage": str(export_group_stage_csv(single)),
        "group_matches": str(export_group_matches_csv(single)),
        "knockout": str(export_knockout_csv(single)),
        "probabilities": str(export_probabilities_csv(probs)),
    }

    return {
        "single_simulation": single,
        "probabilities": probs,
        "exported_files": paths,
    }
