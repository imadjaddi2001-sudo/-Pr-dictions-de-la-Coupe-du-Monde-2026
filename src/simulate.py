"""
Full tournament simulation pipeline.
Runs group stage + knockout stage and exports results to CSV files.
"""
import pandas as pd
import json
from pathlib import Path
from typing import Dict

from src.group_stage import simulate_group_stage, get_qualified_teams
from src.knockout import simulate_knockout_stage

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_full_simulation() -> Dict:
    """
    Run one complete World Cup simulation.
    Returns dict with all results and saves CSVs.
    """
    print("⚽ Simulation Coupe du Monde 2026...")

    # --- GROUP STAGE ---
    print("📊 Phase de groupes...")
    df_tables, df_group_matches = simulate_group_stage()
    slot_map, best_third, qualified = get_qualified_teams(df_tables)

    # --- KNOCKOUT STAGE ---
    print("🏆 Phase à élimination directe...")
    r32_teams = qualified["team"].tolist()
    df_knockout, winner, runner_up = simulate_knockout_stage(r32_teams, slot_map, best_third)

    # --- MERGE ALL MATCHES ---
    # Align group match columns
    group_cols = ["match_id", "group", "stage", "home_team", "away_team",
                  "home_goals", "away_goals", "winner", "note",
                  "home_win_prob", "away_win_prob", "draw_prob",
                  "home_xg", "away_xg"]
    df_group_export = df_group_matches[[c for c in group_cols if c in df_group_matches.columns]].copy()
    df_group_export["round"] = "Group Stage"
    df_group_export["round_label"] = "Group Stage"

    ko_cols = ["match_id", "round", "round_label", "stage", "home_team", "away_team",
               "home_goals", "away_goals", "winner", "note",
               "home_win_prob", "away_win_prob", "draw_prob"]
    df_ko_export = df_knockout[[c for c in ko_cols if c in df_knockout.columns]].copy()

    # --- EXPORT CSVs ---
    paths = {}

    # 1. Group tables
    path_tables = OUTPUT_DIR / "group_tables.csv"
    df_tables.to_csv(path_tables, index=False)
    paths["group_tables"] = str(path_tables)

    # 2. All group matches
    path_group = OUTPUT_DIR / "group_matches.csv"
    df_group_export.to_csv(path_group, index=False)
    paths["group_matches"] = str(path_group)

    # 3. Knockout results
    path_ko = OUTPUT_DIR / "knockout_results.csv"
    df_ko_export.to_csv(path_ko, index=False)
    paths["knockout_results"] = str(path_ko)

    # 4. Full bracket summary
    df_all = pd.concat([df_group_export.assign(stage="Group Stage"),
                        df_ko_export], ignore_index=True)
    path_all = OUTPUT_DIR / "all_matches.csv"
    df_all.to_csv(path_all, index=False)
    paths["all_matches"] = str(path_all)

    # 5. Qualified teams (R32)
    path_qual = OUTPUT_DIR / "qualified_r32.csv"
    qualified[["team", "group", "position", "Pts", "W", "D", "L", "GF", "GA", "GD"]].to_csv(path_qual, index=False)
    paths["qualified_r32"] = str(path_qual)

    # 6. Build bracket JSON for visualization
    bracket = _build_bracket_json(df_group_export, df_ko_export, df_tables, winner, runner_up)

    print(f"\n🏆 VAINQUEUR: {winner}")
    print(f"🥈 Finaliste: {runner_up}")
    print(f"\n📁 Fichiers CSV générés:")
    for k, v in paths.items():
        print(f"  {k}: {v}")

    return {
        "winner": winner,
        "runner_up": runner_up,
        "group_tables": df_tables,
        "group_matches": df_group_export,
        "knockout_results": df_ko_export,
        "qualified": qualified,
        "paths": paths,
        "bracket": bracket,
    }


def _build_bracket_json(df_group, df_ko, df_tables, winner, runner_up) -> Dict:
    """Build a structured bracket dict for the web app."""
    bracket = {
        "winner": winner,
        "runner_up": runner_up,
        "groups": {},
        "rounds": {},
    }

    # Group tables
    for group, gdf in df_tables.groupby("group"):
        bracket["groups"][group] = gdf[["team", "position", "Pts", "W", "D", "L", "GF", "GA", "GD"]].to_dict("records")

    # Knockout rounds
    round_order = ["R32", "R16", "QF", "SF", "3rd", "Final"]
    for rnd in round_order:
        rnd_df = df_ko[df_ko["round"] == rnd]
        if len(rnd_df) == 0:
            continue
        bracket["rounds"][rnd] = rnd_df[[
            "match_id", "home_team", "away_team",
            "home_goals", "away_goals", "winner", "note",
            "home_win_prob", "away_win_prob"
        ]].to_dict("records")

    # Save bracket JSON
    bracket_path = OUTPUT_DIR / "bracket.json"
    with open(bracket_path, "w", encoding="utf-8") as f:
        json.dump(bracket, f, ensure_ascii=False, indent=2)

    return bracket


if __name__ == "__main__":
    result = run_full_simulation()
